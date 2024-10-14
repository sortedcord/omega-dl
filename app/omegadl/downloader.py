import requests
from pathlib import Path
import os
from utils import zip_files, list_files_abs
from objects import Comic, Chapter
from comicxml import ComicInfo, Manga, AgeRating, create_comic_info_xml
import xml.etree.ElementTree as ET
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import numpy as np
from rich.progress import Progress


def zip_chapter(input_dir:Path, output_dir:Path, comic:Comic, chapter:Chapter):
    files = list_files_abs(input_dir)
    out = output_dir / comic.name
    os.makedirs(out, exist_ok=True)
    output = Path( out / f"{comic.name} Vol.{chapter.get_volume(comic)} Ch.{chapter.slug.split('-')[1]}.cbz")
    if os.path.exists(output):
        os.remove(output)
    zip_files(files,output )


def download(url, output_dir, filename=None, overwrite:bool=False):
    if filename is None:
        filename = url.split('/')[-1].split('?')[0]
    if os.path.exists( output_dir / filename) and not overwrite:
        return
    r = requests.get(url)
    with open(output_dir / filename, "wb") as f:
        f.write(r.content)


# FIXME: Fix comic xml output.
def generate_comic_xml(comic:Comic, chapter:Chapter, out_path:Path) -> str:
    comic_info = ComicInfo()
    comic.title = comic.name
    comic.volume = 1
    comic.number = chapter.slug
    # comic.summary = "This is an example comic."
    # comic.year = 2023
    comic.language_iso = "en"
    comic.manga = Manga.YES
    comic.age_rating = AgeRating.X18_PLUS

    root = create_comic_info_xml(comic_info)
    tree = ET.ElementTree(root)
    tree.write(out_path / "ComicInfo.xml", encoding="utf-8", xml_declaration=True)


def download_chapter(comic:Comic, chapter:Chapter, output_dir:Path, library_dir:Path, progress:Progress=None, task=None):

    out = output_dir / "comics" / comic.slug / chapter.slug
    os.makedirs(out, exist_ok=True)

    generate_chapter_cover(comic,chapter, output_dir)
    progress.update(task, advance=1, description="[green]Generating Chapter ComicInfo.xml...")

    # Generate ComicXML
    generate_comic_xml(comic, chapter, out)
    progress.update(task, advance=1, description="[green]Downloading Chapter pages...")

    urls = chapter.pages
    for i,url in enumerate(urls):
        progress.update(task, description=f"[green]Downloading pages [{i+1}/{len(chapter.pages)}]  {chapter.name} - {comic.name[:45]}...")
        # print("Downloading ", url)
        download(url, out)
        progress.update(task, advance=1)

    zip_chapter(out, library_dir, comic, chapter)  
    progress.update(task, advance=1) 


def generate_chapter_cover(comic:Comic, chapter:Chapter, output_dir:Path):

    comic_image_cache_dir:Path = output_dir / "cache" / "images"
    os.makedirs(comic_image_cache_dir, exist_ok=True)

    if chapter.is_breakpoint(comic):
        download(comic.get_cover(chapter), output_dir / "comics" / comic.slug / chapter.slug, filename= "cover.jpg")
        return

    # Download Comic Cover
    download(comic.get_cover(chapter), comic_image_cache_dir, filename= f"{comic.id}_cover{chapter.get_volume(comic)}.jpg")
    thumbnail = Image.open(comic_image_cache_dir / f"{comic.id}_cover{chapter.get_volume(comic)}.jpg")

    # Resize chapter thumbnail, scale height to 1260 keeping aspect ratio
    aspect_ratio = thumbnail.height / thumbnail.width
    new_height = 1260
    new_width = int(new_height / aspect_ratio)
    resized_thumbnail = thumbnail.resize((new_width, new_height), Image.LANCZOS)

    # If width of frame > 900 then apply a vertical crop
    if new_width > 900:
        left = (new_width/2) - (450)
        right = (new_width/2) + (450)
        resized_thumbnail = resized_thumbnail.crop((left, 0, right, 1260)) # left upper right lower
        new_height = 1260

    # Create a new image with the final resolution and paste the resized thumbnail in the center
    final_image = Image.new("RGB", (900, 1260), (0, 0, 0))
    paste_x = (1260 - new_width) // 2
    # paste_y = (900 - new_height) // 2
    final_image.paste(resized_thumbnail, (0, 0))

    # Blur the image
    blurred_image = final_image.filter(ImageFilter.GaussianBlur(radius=30))

    if chapter.thumbnail_url is not None:
        # Download the chapter thumbnail
        download(chapter.thumbnail_url, comic_image_cache_dir, filename= f"{comic.id}_{chapter.id}_cover.jpg")
        overlay = Image.open(comic_image_cache_dir / f"{comic.id}_{chapter.id}_cover.jpg")

        # Resize overlay, scale width to 800 keeping aspect ratio
        overlay_aspect_ratio = overlay.height / overlay.width
        overlay_new_width = 800
        overlay_new_height = int(overlay_new_width * overlay_aspect_ratio)
        resized_overlay = overlay.resize((overlay_new_width, overlay_new_height), Image.LANCZOS)

        mask = Image.new('L', resized_overlay.size, 0)
        draw = ImageDraw.Draw(mask)
        center = (overlay_new_width // 2, overlay_new_height // 2)
        radius = min(center[0], center[1]) + 100
        draw.ellipse([center[0] - radius, center[1] - radius, 
                    center[0] + radius, center[1] + radius], fill=255)

        # Create a gradual fade effect
        mask_np = np.array(mask)
        y, x = np.ogrid[:overlay_new_height, :overlay_new_width]
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        mask_np = np.clip(radius - dist_from_center, 0, 255).astype('uint8')

        # Convert back to PIL Image and apply Gaussian blur for smoother fade
        mask = Image.fromarray(mask_np)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=20))

        # Apply the mask to the overlay
        if resized_overlay.mode != 'RGBA':
            resized_overlay = resized_overlay.convert('RGBA')

        # Apply the mask to the overlay
        resized_overlay.putalpha(mask)

        # Place the overlay on the center of the blurred image
        overlay_x = (900 - overlay_new_width) // 2
        overlay_y = ((1260 - overlay_new_height) // 2) + 200
        blurred_image.paste(resized_overlay, (overlay_x, overlay_y), resized_overlay)

    # Download logo
    logo_url = comic.get_logo()
    download(logo_url, comic_image_cache_dir, filename= f"{comic.id}_logo.png")
    logo = Image.open(comic_image_cache_dir / f"{comic.id}_logo.png")

    # Resize logo, scale width to 600 keeping aspect ratio
    logo_aspect_ratio = logo.height / logo.width
    logo_new_width = 600
    logo_new_height = int(logo_new_width * logo_aspect_ratio)
    resized_logo = logo.resize((logo_new_width, logo_new_height), Image.LANCZOS)

    # Add shadow to the logo
    shadow = Image.new("RGBA", resized_logo.size, (0, 0, 0, 0))
    shadow_drawer = ImageEnhance.Brightness(resized_logo)
    shadow = shadow_drawer.enhance(0.5)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=9))

    # Place logo and shadow on the center of the frame
    logo_x = (900 - logo_new_width) // 2
    logo_y = ((1260 - logo_new_height) // 2) - 240

    blurred_image.paste(shadow, (logo_x + 5, logo_y + 5), shadow)
    blurred_image.paste(resized_logo, (logo_x, logo_y), resized_logo)

    # Add chapter number to the bottom right corner
    chapter_number = chapter.name.replace("Chapter ","")
    draw = ImageDraw.Draw(blurred_image)

    # Load a font (you may need to specify the path to a font file on your system)
    try:
        font = ImageFont.truetype("Brush Script.ttf", 110)
    except IOError:
        font = ImageFont.load_default()

    text = f"#{chapter_number}"
    text_width = draw.textlength(text, font=font)
    text_height = 110

    # Position text in bottom right with 10px margin
    text_x = 900 - text_width - 70
    text_y = 1260 - text_height - 30

    # Add text shadow
    shadow_offset = 2
    draw.text((text_x + shadow_offset, text_y + shadow_offset), text, font=font, fill=(0, 0, 0, 20))

    # Add main text
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    # Export image as image.jpg
    blurred_image.save(output_dir / "comics" / comic.slug / chapter.slug / "cover.jpg", "JPEG", quality=95)


