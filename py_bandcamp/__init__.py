from bs4 import BeautifulSoup
import json
from py_bandcamp.session import SESSION as requests
from py_bandcamp.utils import extract_ldjson_blob, get_props, extract_blob


class BandCamper:
    @staticmethod
    def tags(tag_list=True):
        data = extract_blob("https://bandcamp.com/tags")
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
        url = 'http://bandcamp.com/tag/' + str(tag)
        data = extract_blob(url, params=params)

        related_tags = [{"name": t["norm_name"], "score": t["relation"]}
                        for t in data["hub"].pop("related_tags")]

        collections, dig_deeper = data["hub"].pop("tabs")
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
                result["image"] = "https://f4.bcbits.com/img/a{art_id}_1.jpg". \
                    format(art_id=result.pop("art_id"))
                for _ in _to_remove:
                    if _ in result:
                        result.pop(_)
                result["related_tags"] = related_tags
                result["collection"] = c["name"]
                if "tralbum_url" in result:
                    result["album_url"] = result.pop("tralbum_url")
                # TODO featured track object
                yield BandcampTrack(result, scrap=False)

        for k in dig_deeper:
            for result in dig_deeper[k]["items"]:
                for _ in _to_remove:
                    if _ in result:
                        result.pop(_)
                result["related_tags"] = related_tags
                result["collection"] = "dig_deeper"
                if "tralbum_url" in result:
                    result["album_url"] = result.pop("tralbum_url")
                # TODO featured track object
                yield BandcampTrack(result, scrap=False)

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
            item_type = item.find('div', class_='itemtype').text.strip().lower()
            if item_type == "album" and albums:
                data = BandCamper._parse_album(item)
            elif item_type == "track" and tracks:
                data = BandCamper._parse_track(item)
            elif item_type == "artist" and artists:
                data = BandCamper._parse_artist(item)
            elif item_type == "label" and labels:
                data = BandCamper._parse_label(item)
            else:
                continue
            #data["type"] = type
            yield data
            seen.append(data)
        if not len(seen):
            return  # no more pages
        for item in BandCamper.search(name, page=page + 1, albums=albums,
                                      tracks=tracks, artists=artists,
                                      labels=labels):
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
        data = BandCamper.get_stream_data(url)
        for p in data['additionalProperty']:
            if p['name'] == 'file_mp3-128':
                return p["value"]
        return url

    @staticmethod
    def get_stream_data(url):

        txt_string = requests.get(url).text

        json_blob = txt_string. \
            split('<script type="application/ld+json">')[-1]. \
            split("</script>")[0]

        data = json.loads(json_blob)
        from pprint import pprint
        pprint(data)

        artist_data = data['byArtist']
        album_data = data['inAlbum']
        result = {
            "categories": data["@type"],
            'album_name': album_data['name'],
            'artist': artist_data['name'],
            'image': data['image'],
            "title": data['name'],
            "url": url,
            "tags": data['keywords'].split(", ") + data["tags"]
        }

        for p in data['additionalProperty']:
            if p['name'] == 'file_mp3-128':
                result["stream"] = p["value"]
            if p['name'] == 'duration_secs':
                result["length"] = p["value"] * 1000

        return result

    @staticmethod
    def _parse_label(item):
        art = item.find("div", {"class": "art"}).find("img")
        if art:
            art = art["src"]
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
        return BandcampLabel(data)

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
        data = {"name": name, "genre": genre, "location": location,
                "tags": tags, "url": url, "image": art, "albums": []
                }

        return BandcampArtist(data)

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
        return BandcampTrack(data)

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
        return BandcampAlbum(data, scrap=False)


class BandcampTrack:
    def __init__(self, data, scrap=True):
        self._url = data.get("url")
        self._data = data or {}
        self._page_data = {}
        if scrap:
            self.scrap()
        if not self.url:
            raise ValueError("bandcamp url is not set")

    def scrap(self):
        self._page_data = self.get_track_data(self.url)
        return self._page_data

    @staticmethod
    def from_url(url):
        return BandcampTrack({"url": url})

    @property
    def url(self):
        return self._url or self.data.get("url")

    @property
    def album(self):
        return self.get_album(self.url)

    @property
    def artist(self):
        return self.get_artist(self.url)

    @property
    def data(self):
        for k, v in self._page_data.items():
            self._data[k] = v
        return self._data

    @property
    def title(self):
        return self.data.get("title") or self.data.get("name") or \
               self.url.split("/")[-1]

    @property
    def image(self):
        return self.data.get("image")

    @property
    def track_num(self):
        return self.data.get("tracknum")

    @property
    def stream(self):
        return self.data.get("file_mp3-128")

    @staticmethod
    def get_album(url):
        data = extract_ldjson_blob(url, clean=True)
        if data.get('inAlbum'):
            return BandcampAlbum({
                "title": data['inAlbum'].get('name'),
                "url": data['inAlbum'].get('id', url).split("#")[0],
                'type': data['inAlbum'].get("type"),
            })

    @staticmethod
    def get_artist(url):
        data = extract_ldjson_blob(url, clean=True)
        d = data.get("byArtist")
        if d:
            return BandcampArtist({
                "title": d.get('name'),
                "url": d.get('id', url).split("#")[0],
                'genre': d.get('genre'),
                "artist_type": d.get('type')
            }, scrap=False)
        return None

    @staticmethod
    def get_track_data(url):
        data = extract_ldjson_blob(url, clean=True)
        track = {
            'dateModified': data.get('dateModified'),
            'datePublished': data.get('datePublished'),
            "url": data.get('id') or url,
            "title": data.get("name"),
            "type": data.get("type"),
            'image': data.get('image'),
            'keywords': data.get('keywords', "").split(", ")
        }
        for k, v in get_props(data).items():
            track[k] = v
        return track

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.title

    def __str__(self):
        return self.url


class BandcampAlbum:
    def __init__(self, data, scrap=True):
        self._url = data.get("url")
        self._data = data or {}
        self._page_data = {}
        if scrap:
            self.scrap()
        if not self.url:
            raise ValueError("bandcamp url is not set")

    def scrap(self):
        self._page_data = self.get_album_data(self.url)
        return self._page_data

    @staticmethod
    def from_url(url):
        return BandcampAlbum({"url": url})

    @property
    def image(self):
        return self.data.get("image")

    @property
    def url(self):
        return self._url or self.data.get("url")

    @property
    def title(self):
        return self.data.get("title") or self.data.get("name") or \
               self.url.split("/")[-1]

    @property
    def releases(self):
        return self.get_releases(self.url)

    @property
    def artist(self):
        return self.get_artist(self.url)

    @property
    def keywords(self):
        return self.data.get("keywords") or []

    @property
    def tracks(self):
        return self.get_tracks(self.url)

    @property
    def featured_track(self):
        if not len(self.tracks):
            return None
        num = self.data.get('featured_track_num', 1) or 1
        return self.tracks[int(num) - 1]

    @property
    def comments(self):
        return self.get_comments(self.url)

    @property
    def data(self):
        for k, v in self._page_data.items():
            self._data[k] = v
        return self._data

    @staticmethod
    def get_releases(url):
        data = extract_ldjson_blob(url, clean=True)
        releases = []
        for d in data.get("albumRelease", []):
            release = {
                "description": d.get("description"),
                'image': d.get('image'),
                "title": d.get('name'),
                "url": d.get('id', url).split("#")[0],
                'format': d.get('musicReleaseFormat'),
            }
            releases.append(release)
        return releases

    @staticmethod
    def get_artist(url):
        data = extract_ldjson_blob(url, clean=True)
        d = data.get("byArtist")
        if d:
            return BandcampArtist({
                "description": d.get("description"),
                'image': d.get('image'),
                "title": d.get('name'),
                "url": d.get('id', url).split("#")[0],
                'genre': d.get('genre'),
                "artist_type": d.get('type')
            }, scrap=False)
        return None

    @staticmethod
    def get_tracks(url):
        data = extract_ldjson_blob(url, clean=True)
        if not data.get("track"):
            return []

        data = data['track']

        tracks = []

        for d in data.get('itemListElement', []):
            d = d['item']
            track = {
                "title": d.get('name'),
                "url": d.get('id') or url,
                'type': d.get('type'),
            }
            for k, v in get_props(d).items():
                track[k] = v
            tracks.append(BandcampTrack(track, scrap=False))
        return tracks

    @staticmethod
    def get_comments(url):
        data = extract_ldjson_blob(url, clean=True)
        comments = []
        for d in data.get("comment", []):
            comment = {
                "text": d["text"],
                'image': d["author"].get("image"),
                "author": d["author"]["name"]
            }
            comments.append(comment)
        return comments

    @staticmethod
    def get_album_data(url):
        data = extract_ldjson_blob(url, clean=True)
        props = get_props(data)
        return {
            'dateModified': data.get('dateModified'),
            'datePublished': data.get('datePublished'),
            'description': data.get('description'),
            "url": data.get('id') or url,
            "title": data.get("name"),
            "type": data.get("type"),
            "n_tracks": data.get('numTracks'),
            'image': data.get('image'),
            'featured_track_num': props.get('featured_track_num'),
            'keywords': data.get('keywords', "").split(", ")
        }

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.title

    def __str__(self):
        return self.url


class BandcampLabel:
    def __init__(self, data, scrap=True):
        self._url = data.get("url")
        self._data = data or {}
        self._page_data = {}
        if scrap:
            self.scrap()
        if not self.url:
            raise ValueError("bandcamp url is not set")

    def scrap(self):
        self._page_data = {}  # TODO
        return self._page_data

    @staticmethod
    def from_url(url):
        return BandcampTrack({"url": url})

    @property
    def url(self):
        return self._url or self.data.get("url")

    @property
    def data(self):
        for k, v in self._page_data.items():
            self._data[k] = v
        return self._data

    @property
    def name(self):
        return self.data.get("title") or self.data.get("name") or \
               self.url.split("/")[-1]

    @property
    def location(self):
        return self.data.get("location")

    @property
    def tags(self):
        return self.data.get("tags") or []

    @property
    def image(self):
        return self.data.get("image")

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.name

    def __str__(self):
        return self.url


class BandcampArtist:
    def __init__(self, data, scrap=True):
        self._url = data.get("url")
        self._data = data or {}
        self._page_data = {}
        if scrap:
            self.scrap()

    def scrap(self):
        self._page_data = {}  # TODO
        return self._page_data

    @property
    def featured_album(self):
        return BandcampAlbum.from_url(self.url + "/releases")

    @property
    def featured_track(self):
        if not self.featured_album:
            return None
        return self.featured_album.featured_track

    @staticmethod
    def get_albums(url):
        albums = []
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        for album in soup.find_all("a"):
            album_url = album.find("p", {"class": "title"})
            if album_url:
                title = album_url.text.strip()
                art = album.find("div", {"class": "art"}).find("img")["src"]
                album_url = url + album["href"]
                album = BandcampAlbum({"album_name": title,
                                       "image": art,
                                       "url": album_url})
                albums.append(album)
        return albums

    @property
    def albums(self):
        return self.get_albums(self.url)

    @staticmethod
    def from_url(url):
        return BandcampTrack({"url": url})

    @property
    def url(self):
        return self._url or self.data.get("url")

    @property
    def data(self):
        for k, v in self._page_data.items():
            self._data[k] = v
        return self._data

    @property
    def name(self):
        return self.data.get("title") or self.data.get("name") or \
               self.url.split("/")[-1]

    @property
    def location(self):
        return self.data.get("location")

    @property
    def genre(self):
        return self.data.get("genre")

    @property
    def tags(self):
        return self.data.get("tags") or []

    @property
    def image(self):
        return self.data.get("image")

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.name

    def __str__(self):
        return self.url

    def __eq__(self, other):
        if str(self) == str(other):
            return True
        return False

