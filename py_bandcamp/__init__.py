from bs4 import BeautifulSoup
import json
import requests


class BandCamper:
    @staticmethod
    def _extract_blob(blob):
        # TODO theres gotta be a nicer way to extract blob
        if "<div data-blob='" in blob:
            json_data = \
                blob.split("<div data-blob='")[1].split(
                    "' id=\"pagedata\"></div>")[0]
        else:
            json_data = \
                blob.split("div data-blob=\"")[1].split(
                    "\" id=\"pagedata\"></div>")[0].replace("&quot;", '"')
        return json_data

    @staticmethod
    def tags(tag_list=True):
        r = requests.get("https://bandcamp.com/tags").content
        soup = BeautifulSoup(r, "html.parser")

        blob = str(soup.find("div"))
        json_data = BandCamper._extract_blob(blob)

        data = json.loads(json_data)
        tags = {"genres": data["signup_params"]["genres"],
                "subgenres": data["signup_params"]["subgenres"]}
        if not tag_list:
            return tags
        tag_list = []
        for genre in tags["subgenres"]:
            tag_list.append(genre)
            tag_list += [sub["norm_name"] for sub in tags["subgenres"][genre]]
        return tag_list

    @staticmethod
    def search_tag(tag, page=1, pop_date=1):
        tag = tag.strip().replace(" ", "-").lower()
        if tag not in BandCamper.tags():
            return []
        params = {"page": page, "sort_field": pop_date}
        response = requests.get('http://bandcamp.com/tag/' + str(tag),
                                params=params)
        html_doc = response.content
        soup = BeautifulSoup(html_doc, 'html.parser')

        blob = str(soup.find("div"))
        json_data = BandCamper._extract_blob(blob)

        dump = json.loads(json_data)["hub"]

        related_tags = [{"name": t["norm_name"], "score": t["relation"]}
                        for t in dump.pop("related_tags")]
        collections, dig_deeper = dump.pop("tabs")
        dig_deeper = dig_deeper["dig_deeper"]["results"]
        collections = collections["collections"]

        _to_remove = ['custom_domain', 'custom_domain_verified', "item_type",
                      'packages', 'slug_text', 'subdomain', 'is_preorder',
                      'item_id', 'num_comments', 'tralbum_id', 'band_id',
                      'tralbum_type', 'genre_id', 'audio_track_id']

        for c in collections:
            if c["name"] == "bc_dailys":
                continue
            for result in c["items"]:
                result["image"] = "https://f4.bcbits.com/img/a{art_id}_1.jpg".\
                    format(art_id=result.pop("art_id"))
                for _ in _to_remove:
                    if _ in result:
                        result.pop(_)
                result["related_tags"] = related_tags
                result["collection"] = c["name"]
                if "tralbum_url" in result:
                    result["album_url"] = result.pop("tralbum_url")
                yield result
        for k in dig_deeper:
            for result in dig_deeper[k]["items"]:
                for _ in _to_remove:
                    if _ in result:
                        result.pop(_)
                result["related_tags"] = related_tags
                result["collection"] = "dig_deeper"
                if "tralbum_url" in result:
                    result["album_url"] = result.pop("tralbum_url")
                yield result

    @staticmethod
    def search_albums(album_name):
        for album in BandCamper.search(album_name, albums=True, tracks=False,
                                       artists=False, labels=False):
            yield album

    @staticmethod
    def search_tracks(track_name):
        for t in BandCamper.search(track_name, albums=False, tracks=True,
                                   artists=False, labels=False):
            yield t

    @staticmethod
    def search_artists(artist_name):
        for a in BandCamper.search(artist_name, albums=False, tracks=False,
                                   artists=True, labels=False):
            yield a

    @staticmethod
    def search_labels(label_name):
        for a in BandCamper.search(label_name, albums=False, tracks=False,
                                   artists=False, labels=True):
            yield a

    @staticmethod
    def search(name, page=1, albums=True, tracks=True, artists=True,
               labels=False):
        params = {"page": page, "q": name}
        response = requests.get('http://bandcamp.com/search', params=params)
        html_doc = response.content
        soup = BeautifulSoup(html_doc, 'html.parser')

        seen = []
        for item in soup.find_all("li", class_="searchresult"):
            type = item.find('div', class_='itemtype').text.strip().lower()
            if type == "album" and albums:
                data = BandCamper._parse_album(item)
            elif type == "track" and tracks:
                data = BandCamper._parse_track(item)
            elif type == "artist" and artists:
                data = BandCamper._parse_artist(item)
            elif type == "label" and labels:
                data = BandCamper._parse_label(item)
            else:
                continue
            data["type"] = type
            yield data
            seen.append(data)
        if not len(seen):
            return  # no more pages
        for item in BandCamper.search(name, page=page + 1, albums=albums,
                                      tracks=tracks,
                                      artists=artists, labels=labels):
            if item in seen:
                return  # duplicate data, fail safe out of loops
            yield item

    @staticmethod
    def get_track_lyrics(track_url):
        track_page = requests.get(track_url)
        track_soup = BeautifulSoup(track_page.text, 'html.parser')
        track_lyrics = track_soup.find("div", {"class": "lyricsText"})
        if track_lyrics:
            return track_lyrics.text

        return "lyrics unavailable"

    @staticmethod
    def get_streams(urls):
        if not isinstance(urls, list):
            urls = [urls]
        direct_links = [BandCamper.get_stream_url(url) for url in urls]
        return direct_links

    @staticmethod
    def get_stream_url(url):
        return BandCamper.get_stream_data(url)["stream"]

    @staticmethod
    def get_stream_data(url):
        txt_string = requests.get(url).text

        search = "var TralbumData = "
        startIndex = txt_string.find(search) + len(search)

        endIndex = txt_string.find(";", startIndex)
        trackinfo = txt_string[startIndex:endIndex]

        search = "trackinfo:"
        startIndex = trackinfo.find("trackinfo:") + len(search)
        endIndex = trackinfo.find("],", startIndex) + len("]")

        parsed = json.loads(trackinfo[startIndex:endIndex])[0]
        return {"stream": parsed["file"]["mp3-128"],
                "featured_track_title": parsed["title"]}

    @staticmethod
    def _parse_label(item):
        art = item.find("div", {"class": "art"}).find("img")["src"]
        name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[
            0]
        location = item.find('div', class_='subhead').text.strip()
        try:
            tags = item.find('div', class_='tags').text \
                .replace("tags:", "").split(",")
            tags = [t.strip().lower() for t in tags]
        except:  # sometimes missing
            tags = []

        data = {"name": name, "location": location,
                "tags": tags, "url": url, "image": art
                }
        return data

    @staticmethod
    def _parse_artist(item):
        name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[
            0]
        genre = item.find('div', class_='genre').text.strip().replace(
            "genre: ", "")
        location = item.find('div', class_='subhead').text.strip()
        try:
            tags = item.find('div', class_='tags').text \
                .replace("tags:", "").split(",")
            tags = [t.strip().lower() for t in tags]
        except:  # sometimes missing
            tags = []
        art = item.find("div", {"class": "art"}).find("img")["src"]
        data = {"artist": name, "genre": genre, "location": location,
                "tags": tags, "url": url, "image": art, "albums": []
                }

        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        for album in soup.find_all("a"):
            album_url = album.find("p", {"class": "title"})
            if album_url:
                title = album_url.text.strip()
                art = album.find("div", {"class": "art"}).find("img")["src"]
                album_url = url + album["href"]
                data["albums"].append({"album_name": title,
                                       "image": art,
                                       "url": album_url})
        return data

    @staticmethod
    def _parse_track(item):
        track_name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[
            0]
        album_name, artist = item.find('div', class_='subhead').text.strip(

        ).split("by")
        album_name = album_name.strip().replace("from ", "")
        artist = artist.strip()
        released = item.find('div', class_='released').text.strip().replace(
            "released ", "")
        try:
            tags = item.find('div', class_='tags').text \
                .replace("tags:", "").split(",")
            tags = [t.strip().lower() for t in tags]
        except:  # sometimes missing
            tags = []

        art = item.find("div", {"class": "art"}).find("img")["src"]
        data = {"track_name": track_name, "released": released, "url": url,
                "tags": tags, "album_name": album_name, "artist": artist,
                "image": art
                }
        try:
            data.update(BandCamper.get_stream_data(url))
        except:
            pass
        return data

    @staticmethod
    def _parse_album(item):
        art = item.find("div", {"class": "art"}).find("img")["src"]
        album_name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[
            0]
        lenght = item.find('div', class_='length').text.strip()
        tracks, minutes = lenght.split(",")
        tracks = tracks.replace(" tracks", "").replace(" track", "").strip()
        minutes = minutes.replace(" minutes", "").strip()
        released = item.find('div', class_='released').text.strip().replace(
            "released ", "")
        tags = item.find('div', class_='tags').text.replace("tags:",
                                                            "").split(",")
        tags = [t.strip().lower() for t in tags]
        artist = item.find("div", {"class": "subhead"}).text.strip()
        if artist.startswith("by "):
            artist = artist[3:]
        data = {"album_name": album_name,
                "length": lenght,
                "minutes": minutes,
                "url": url,
                "image": art,
                "artist": artist,
                "track_number": tracks,
                "released": released,
                "tags": tags
                }
        try:
            data.update(BandCamper.get_stream_data(url))
        except:
            pass
        return data

