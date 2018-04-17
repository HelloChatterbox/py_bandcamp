from bs4 import BeautifulSoup
import json
import sys
if sys.version_info[0] < 3:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen
import requests


class BandCamper(object):
    def search_tag(self, tag, page=1, pop_date=1):
        response = urlopen(
            'http://bandcamp.com/tag/' + str(tag) + '?page=' + str(
                page) + '&sort_field=' + str(pop_date))
        html_doc = response.read()

        soup = BeautifulSoup(html_doc, "lxml")

        for item in soup.find_all("li", class_="item"):
            band = item.find('div', class_='itemsubtext').text
            data = {"artist": band,
                     "name": item.find('div', class_='itemtext').text,
                     "url": item.find('a').get('href')}
            yield data
        yield self.search_tag(tag, page + 1, pop_date)

    def search_albums(self, album_name):
        for album in self.search(album_name, albums=True, tracks=False,
                                 artists=False, labels=False):
            yield album

    def search_tracks(self, track_name):
        for t in self.search(track_name, albums=False, tracks=True,
                             artists=False, labels=False):
            yield t

    def search_artists(self, artist_name):
        for a in self.search(artist_name, albums=False, tracks=False,
                             artists=True, labels=False):
            yield a

    def search_labels(self, label_name):
        for a in self.search(label_name, albums=False, tracks=False,
                             artists=False, labels=True):
            yield a

    def search(self, name, page=1, albums=True, tracks=True, artists=True,
               labels=True):
        response = urlopen(
            'http://bandcamp.com/search?page=' + str(page) +
            '&q=' + name.replace(" ", "%20"))
        html_doc = response.read()

        soup = BeautifulSoup(html_doc, "lxml")

        for item in soup.find_all("li", class_="searchresult"):
            type = item.find('div', class_='itemtype').text.strip().lower()
            if type == "album" and albums:
                data = self._parse_album(item)
            elif type == "track" and tracks:
                data = self._parse_track(item)
            elif type == "artist" and artists:
                data = self._parse_artist(item)
            elif type == "label" and labels:
                data = self._parse_label(item)
            else:
                continue
            data["type"] = type
            yield data
        yield self.search(name, page=page + 1, albums=albums, tracks=tracks,
                          artists=artists, labels=labels)

    def get_track_lyrics(self, track_url):
        track_page = requests.get(track_url)
        track_soup = BeautifulSoup(track_page.text, "lxml")
        track_lyrics = track_soup.find("div", {"class": "lyricsText"})
        if track_lyrics:
            return track_lyrics.text

        return "lyrics unavailable"

    def get_streams(self, urls):
        if not isinstance(urls, list):
            urls = [urls]
        direct_links = [self.get_stream_url(url) for url in urls]
        return direct_links

    def get_stream_url(self, url):
        response = urlopen(url)
        string = response.read()
        search = "var TralbumData = "
        startIndex = string.find(search) + len(search)
        endIndex = string.find(";", startIndex)
        trackinfo = string[startIndex:endIndex]

        search = "trackinfo:"
        startIndex = trackinfo.find("trackinfo:") + len(search)
        endIndex = trackinfo.find("],", startIndex) + len("]")

        parsed = json.loads(trackinfo[startIndex:endIndex])[0]
        stream_url = parsed["file"]["mp3-128"]

        return stream_url

    def _parse_label(self, item):
        name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[0]
        location = item.find('div', class_='subhead').text.strip()
        try:
            tags = item.find('div', class_='tags').text\
                .replace("tags:", "").split(",")
            tags = [t.strip().lower() for t in tags]
        except: # sometimes missing
            tags = []

        data = {"name": name, "location": location,
                "tags": tags, "url": url
                }
        return data

    def _parse_artist(self, item):
        name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[0]
        genre = item.find('div', class_='genre').text.strip().replace(
            "genre: ", "")
        location = item.find('div', class_='subhead').text.strip()
        try:
            tags = item.find('div', class_='tags').text\
                .replace("tags:", "").split(",")
            tags = [t.strip().lower() for t in tags]
        except: # sometimes missing
            tags = []

        data = {"name": name, "genre": genre, "location": location,
                "tags": tags, "url": url
                }
        return data

    def _parse_track(self, item):
        track_name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[0]
        album_name, artist = item.find('div', class_='subhead').text.strip(

        ).split("by")
        album_name = album_name.strip().replace("from ", "")
        artist = artist.strip()
        released = item.find('div', class_='released').text.strip().replace(
            "released ", "")
        try:
            tags = item.find('div', class_='tags').text\
                .replace("tags:", "").split(",")
            tags = [t.strip().lower() for t in tags]
        except: # sometimes missing
            tags = []

        data = {"track_name": track_name, "released": released, "url": url,
                "tags": tags, "album_name": album_name, "artist": artist
                }
        return data

    def _parse_album(self, item):
        album_name = item.find('div', class_='heading').text.strip()
        url = item.find('div', class_='heading').find('a')['href'].split("?")[0]
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
