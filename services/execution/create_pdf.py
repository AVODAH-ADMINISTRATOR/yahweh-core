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

images = [Image.open(s).convert("RGB") for s in slides]
images[0].save("Avodah_Sunday_Deck.pdf", save_all=True, append_images=images[1:])
