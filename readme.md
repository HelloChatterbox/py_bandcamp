## py bandcamp

for your [bandcamp](https://bandcamp.com) hipster music scrapping needs

## install

    pip install py_bandcamp

## usage

    from py_bandcamp import BandCamper

    b = BandCamper()

    for item in b.search_albums_by_tag("stoner"):
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