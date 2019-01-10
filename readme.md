## py bandcamp
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1QJNhKM8tVv62XSUrST2vnaMXh5ADSyYP8)](https://en.cryptobadges.io/donate/1QJNhKM8tVv62XSUrST2vnaMXh5ADSyYP8)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://paypal.me/jarbasai)
<span class="badge-patreon"><a href="https://www.patreon.com/jarbasAI" title="Donate to this project using Patreon"><img src="https://img.shields.io/badge/patreon-donate-yellow.svg" alt="Patreon donate button" /></a></span>
[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/JarbasAl)

for your [bandcamp](https://bandcamp.com) hipster music scrapping needs

## install

    pip install py_bandcamp

## usage

    from py_bandcamp import BandCamper

    b = BandCamper()

    for item in b.search_tag("stoner"):
        print item
        break

    for item in b.search_artists("Scythe"):
        print item
        break

    for item in b.search_albums("Center Of All Infinity"):
        print item
        break

    for item in b.search_tracks("Astronaut Problems"):
        print item
        break

    for item in b.search_labels("evil"):
        print item
        break

    for item in b.search("cyber punk"):
        print item
        break


    tracks = b.parse_bandcamp_url("https://lordpiggy.bandcamp.com/track/in-the-name-of-porn-grind-on")
    streams = b.get_streams("https://hellpatrol.bandcamp.com/track/satanic-storm")

    print tracks[0].keys()
    print streams

    """
    output:

    {'url': 'https://naxatras.bandcamp.com/album/iii', 'name': u'III', 'artist': u'Naxatras'}
    {'name': u'Scythelord', 'tags': [u'thrash metal', u'metal', u'death metal'], 'url': 'https://scythelordofficial.bandcamp.com', 'location': u'hell, Michigan', 'genre': u'Metal', 'type': u'artist'}
    {'tags': [u'sweden', u'space rock', u'spacerock', u'gothenburg', u'psychedelic rock', u'psych', u'rock', u'stoner'], 'url': 'https://yurigagarinswe.bandcamp.com/album/at-the-center-of-all-infinity', 'type': u'album', 'track_number': u'6', 'released': u'02 December 2015', 'length': u'6 tracks, 40 minutes', 'album_name': u'At The Center Of All Infinity', 'minutes': u'40'}
    {'artist': u'Dead Unicorn', 'url': 'https://deadunicorn.bandcamp.com/track/astronaut-problems', 'tags': [], 'released': u'26 May 2017', 'track_name': u'Astronaut Problems', 'album_name': u'Aliens', 'type': u'track'}
    {'url': 'https://versusevil.bandcamp.com', 'tags': [], 'type': u'label', 'name': u'Versus Evil', 'location': u'Maryland'}
    {'artist': u'Floodlore', 'url': 'https://floodlore.bandcamp.com/track/cyber-punk', 'tags': [], 'released': u'26 January 2018', 'track_name': u'Cyber Punk', 'album_name': u'When It Was Forged: Chapters 1 and 2', 'type': u'track'}
    ['album', 'album_url', 'track_name', 'artist', 'url', 'artwork_url', 'year', 'tags', 'track_number']
    [u'https://t4.bcbits.com/stream/5af2fa61869d06b9304470860b2dd9c2/mp3-128/3632181075?p=0&ts=1523339746&t=792b74d8c325babdc5077041ad2a4dda24bb8362&token=1523339746_7a4f055c7ecb5edc5137149b4e6fdfaae42f2365']

    """


