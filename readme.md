## py bancamp

for your hipster music scrapping needs

## install

    pip install py_bandcamp

## usage

    b = BandCamper()

    for item in b.search_tags("black metal"):
        print item
        break

    for item in b.search_artists("Sergeant Hamster"):
        print item
        break

    for item in b.search_albums("At The Center Of All Infinity"):
        print item
        break

    for item in b.search_tracks("Astronaut Problems"):
        print item
        break