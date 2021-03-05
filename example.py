from py_bandcamp import BandCamper, BandcampAlbum, BandcampTrack


url = "https://deadunicorn.bandcamp.com/track/astronaut-problems"
track = BandcampTrack.from_url(url)
print(track.stream)
print(track.data)
print(track.artist.data)
print(track.album.data)
print(track.album.featured_track.stream)

album = BandcampAlbum.from_url("https://naxatras.bandcamp.com/album/iii")
print(album.data)
print(album.artist)
print(album.releases)
print(album.comments)
print([t.data for t in album.tracks])

tag_list = BandCamper.tags()
tags = BandCamper.search_tag('black-metal')
albums = BandCamper.search_albums('black-metal')
tracks = BandCamper.search_tracks('astronaut problems')
labels = BandCamper.search_labels("black")
artists = BandCamper.search_artists('Planet of the Dead')

url = "https://perturbator.bandcamp.com/music"
# TODO parse these urls also