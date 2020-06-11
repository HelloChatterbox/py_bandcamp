from bs4 import BeautifulSoup
import json
import requests


class BandCamper:
    @staticmethod
    def tags(tag_list=True):
        r = requests.get("https://bandcamp.com/tags").content
        soup = BeautifulSoup(r, "html.parser")

        # TODO theres gotta be a nicer way to extract blob
        blob = str(soup.find("div"))
        json_data = \
            blob.split("<div data-blob='")[1].split(
                "' id=\"pagedata\"></div>")[0]

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

        # TODO theres gotta be a nicer way to extract blob
        blob = str(soup.find("div"))
        json_data = \
            blob.split("div data-blob=\"")[1].split(
                "\" id=\"pagedata\"></div>")[0].replace("&quot;", '"')
        dump = json.loads(json_data)["hub"]

        related_tags = [{"name": t["norm_name"], "score": t["relation"]}
                        for t in dump.pop("related_tags")]
        collections, dig_deeper = dump.pop("tabs")
        dig_deeper = dig_deeper["dig_deeper"]["results"]
        collections = collections["collections"]

        _to_remove = ['custom_domain', 'custom_domain_verified',"item_type",
                      'packages', 'slug_text', 'subdomain', 'is_preorder',
                      'item_id', 'num_comments', 'tralbum_id', 'band_id',
                      'tralbum_type', 'art_id', 'genre_id', 'audio_track_id']

        for c in collections:
            if c["name"] == "bc_dailys":
                continue
            for result in c["items"]:
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
               labels=True):
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
        txt_string = requests.get(url).text
        search = "var TralbumData = "
        startIndex = txt_string.find(search) + len(search)

        endIndex = txt_string.find(";", startIndex)
        trackinfo = txt_string[startIndex:endIndex]

        search = "trackinfo:"
        startIndex = trackinfo.find("trackinfo:") + len(search)
        endIndex = trackinfo.find("],", startIndex) + len("]")

        parsed = json.loads(trackinfo[startIndex:endIndex])[0]
        stream_url = parsed["file"]["mp3-128"]

        return stream_url

    @staticmethod
    def _parse_label(item):
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
                "tags": tags, "url": url
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

        data = {"name": name, "genre": genre, "location": location,
                "tags": tags, "url": url
                }
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

        data = {"track_name": track_name, "released": released, "url": url,
                "tags": tags, "album_name": album_name, "artist": artist
                }
        return data

    @staticmethod
    def _parse_album(item):
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
        data = {"album_name": album_name,
                "length": lenght, "minutes": minutes, "url": url,
                "track_number": tracks, "released": released, "tags": tags
                }
        return data
