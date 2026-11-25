import sys
sys.path.insert(0, "src/testing")
from ascii_to_image_no_entities import render_room, render_ascii, render_ids

# objects from : dungeons, D1 tail cave, room 10C
ids = [
  ["03", "03", "25", "21", "21", "21", "21", "21", "21", "26"],
  ["03", "25", "29", "01", "B0", "B0", "B0", "01", "01", "24"],
  ["03", "23", "01", "B0", "0F", "0F", "0F", "B0", "B0", "24"],
  ["03", "23", "01", "0F", "A0", "0F", "0F", "0F", "0F", "42"],
  ["03", "23", "01", "0F", "0F", "0F", "0F", "0F", "0F", "24"],
  ["03", "23", "01", "AF", "0F", "0F", "0F", "AF", "AF", "24"],
  ["03", "27", "2B", "01", "AF", "AF", "AF", "01", "01", "24"],
  ["03", "03", "27", "22", "22", "22", "22", "22", "22", "28"],
]
img = render_ids(ids, "dungeons", "D1_tail_cave")

img.save("./src/testing/out.png") # img è un'immagine PIL 160x128
img.show()



""" 
#################################################################################################
qui sotto per provare render_room e render_ascii
"""
# si sceglie un ID di una stanza casuale, che viene trovata in autonomia dal codice
# l'immagine finale mostrata a sinistra l'immagine della stanza originale e a destra quella ricostruita dall'ascii
# 0FA 101 202 2F7 301
#img = render_room("0FA", compare=True)      # originale | ricostruzione, affiancati


# render ascii riceve una lista di 8 stringhe di 10 caratteri e la trasforma in immagine
rows = ["          ",
        "   #####  ",
        "   #...#  ",
        "~~###.###~",
        "~###E.###~",
        "###.....==",
        "###.....##",
        "#########."]
#img = render_ascii(rows, group="overworld")    # obbligatorio inserire il gruppo per sapere dove pescare le tile