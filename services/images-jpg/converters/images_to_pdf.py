from PIL import Image

def images_to_pdf(image_paths, out_pdf_path):
    pages = []
    for p in image_paths:
        img = Image.open(p)
        if img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")
        pages.append(img)
    first, rest = pages[0], pages[1:]
    first.save(out_pdf_path, "PDF", resolution=300, save_all=True, append_images=rest)