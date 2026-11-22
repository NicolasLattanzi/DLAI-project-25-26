import sys
sys.path.insert(0, "src/testing")
from ascii_to_image_no_entities import render_room

# si sceglie un ID di una stanza casuale, che viene trovata in autonomia dal codice
# l'immagine finale mostrata a sinistra l'immagine della stanza originale e a destra quella ricostruita dall'ascii

# 0FA 101 202 2F7 301
img = render_room("0FA", compare=True)      # originale | ricostruzione, affiancati
img.save("./src/testing/out.png")           # img è un'immagine PIL 160x128
img.show()
