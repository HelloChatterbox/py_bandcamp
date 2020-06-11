from pprint import pprint as print
from py_bandcamp import BandCamper

b = BandCamper()

streams = b.get_streams("https://naxatras.bandcamp.com/album/iii")

print(streams)


for item in b.search("naxatras"):
    print(item)
    break

for item in b.search_artists("Mayhem"):
    print(item)
    break

for item in b.search_albums("Center Of All Infinity"):
    print(item)
    break

for item in b.search_tracks("Astronaut Problems"):
    print(item)
    break

for item in b.search_tag("black metal"):
    print(item)
    break

for item in b.search_labels("cyber punk"):
    print(item)
    break

""" 
output:

{'url': 'https://naxatras.bandcamp.com/album/iii', 'album_name': u'III', 'artist': u'Naxatras'}
{'name': u'Scythelord', 'tags': [u'metal', u'death metal', u'thrash metal'], 'url': 'https://scythelordofficial.bandcamp.com', 'location': u'hell, Michigan', 'genre': u'Metal', 'type': u'artist'}
{'tags': [u'sweden', u'space rock', u'spacerock', u'gothenburg', u'psychedelic rock', u'psych', u'rock', u'stoner'], 'url': 'https://yurigagarinswe.bandcamp.com/album/at-the-center-of-all-infinity', 'type': u'album', 'track_number': u'6', 'released': u'02 December 2015', 'length': u'6 tracks, 40 minutes', 'album_name': u'At The Center Of All Infinity', 'minutes': u'40'}
{'artist': u'Dead Unicorn', 'url': 'https://deadunicorn.bandcamp.com/track/astronaut-problems', 'tags': [], 'released': u'26 May 2017', 'track_name': u'Astronaut Problems', 'album_name': u'Aliens', 'type': u'track'}
{'url': 'https://versusevil.bandcamp.com', 'tags': [], 'type': u'label', 'name': u'Versus Evil', 'location': u'Maryland'}
[u'https://t4.bcbits.com/stream/5af2fa61869d06b9304470860b2dd9c2/mp3-128/3632181075?p=0&ts=1523332161&t=cffea273a2673fd99ea631987031b5cfd3af1114&token=1523332161_50e298404d47b570eb09b122c042ac7652cbb9a1']

"""



