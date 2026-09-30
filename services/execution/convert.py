import os
from PIL import Image

slides = [
  "avodah_title_slide_1.webp",
  "slide2_hosea_spiritual_adultery.webp",
  "slide3_psalm85_steadfast_love_faithfulness.webp",
  "colossians_slide_design.webp",
  "prayer_reorders_desire_slide.webp",
  "avodah_response_slide.webp",
  "slide7_closing_wheat.webp"
]

def find_files(files):
    found = {}
    for root, dirs, filenames in os.walk(r"C:\Users\scout"):
        if 'AppData' in root or 'AppData' in dirs:
            if 'AppData' in dirs: dirs.remove('AppData')
        for filename in filenames:
            if filename in files and filename not in found:
                found[filename] = os.path.join(root, filename)
        if len(found) == len(files):
            return found
    return found

print("Finding files...")
found = find_files(slides)
print(found)

if len(found) != len(slides):
    print("Could not find all slides.")
else:
    images = [Image.open(found[s]).convert("RGB") for s in slides]
    out_path = os.path.join(os.path.dirname(found[slides[0]]), "Avodah_Sunday_Deck.pdf")
    images[0].save(out_path, save_all=True, append_images=images[1:])
    print("Saved to", out_path)
