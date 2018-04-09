from bs4 import BeautifulSoup
from datetime import datetime
import demjson
import sys
if sys.version_info[0] < 3:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen
import requests
import re


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

    def get_streams(self, urls):
        if isinstance(urls, basestring):
            urls = [urls]
        direct_links = []
        for url in urls:
            tracks = self.parse_bandcamp_url(url)
            for track in tracks:
                direct_links.append(track["url"])
        return direct_links

    def parse_bandcamp_url(self, url, num_tracks=-1):
        if 'bandcamp.com' not in url: # name given
            url = 'https://' + url + '.bandcamp.com/music'

        tracks = []
        album_data = self._get_bandcamp_metadata(url)

        # If it's a list, we're dealing with a list of Album URLs,
        # so we call the scrape_bandcamp_url() method for each one
        if type(album_data) is list:
            for album_url in album_data:
                tracks.append(
                    self.parse_bandcamp_url(album_url, num_tracks))
            return tracks

        artist = album_data["artist"]
        album_name = album_data["album_name"]

        for i, track in enumerate(album_data["trackinfo"]):
            if num_tracks > 0 and i > num_tracks - 1:
                break

            try:
                track_name = track["title"]
                if track["track_num"]:
                    track_number = str(track["track_num"]).zfill(2)
                else:
                    track_number = None

                if not track['file']:
                    continue
                album_year = album_data['album_release_date']
                if album_year:
                    album_year = datetime.strptime(album_year,
                                                   "%d %b %Y %H:%M:%S GMT").year

                data = {
                     "artist": artist,
                     "track_name": track_name,
                     "album": album_name,
                     "year": album_year,
                     "tags": album_data['tags'],
                     "artwork_url": album_data['artFullsizeUrl'],
                     "track_number": track_number,
                     "album_url": album_data['url'],
                     "url": track["file"]["mp3-128"]
                }

                tracks.append(data)

            except Exception as e:
                print(e)
        return tracks

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

    def _get_bandcamp_metadata(self, url):
        request = requests.get(url)
        try:
            sloppy_json = request.text.split("var TralbumData = ")
            sloppy_json = sloppy_json[1].replace('" + "', "")
            sloppy_json = sloppy_json.replace("'", "\'")
            sloppy_json = sloppy_json.split("};")[0] + "};"
            sloppy_json = sloppy_json.replace("};", "}")
            output = demjson.decode(sloppy_json)
        # if the JSON parser failed, we should consider it's a "/music" page,
        # so we generate a list of albums/tracks and return it immediately
        except Exception as e:
            regex_all_albums = r'<a href="(/(?:album|track)/[^>]+)">'
            all_albums = re.findall(regex_all_albums, request.text,
                                    re.MULTILINE)
            album_url_list = list()
            for album in all_albums:
                album_url = re.sub(r'music/?$', '', url) + album
                album_url_list.append(album_url)
            return album_url_list
        # if the JSON parser was successful, use a regex to get all tags
        # from this album/track, join them and set it as the "genre"
        regex_tags = r'<a class="tag" href[^>]+>([^<]+)</a>'
        tags = re.findall(regex_tags, request.text, re.MULTILINE)
        output['tags'] = tags
        # make sure we always get the correct album name, even if this is a
        # track URL (unless this track does not belong to any album, in which
        # case the album name remains set as None.
        output['album_name'] = None
        regex_album_name = r'album_title\s*:\s*"([^"]+)"\s*,'
        match = re.search(regex_album_name, request.text, re.MULTILINE)
        if match:
            output['album_name'] = match.group(1)

        try:
            artUrl = \
            request.text.split("\"tralbumArt\">")[1].split("\">")[0].split(
                "href=\"")[1]
            output['artFullsizeUrl'] = artUrl
        except:
            output['artFullsizeUrl'] = None

        return output

