import requests
from pathlib import Path
import json
import os
from utils import zip_files, list_files_abs
from objects import Comic, Chapter
from comicxml import ComicInfo, Manga, AgeRating, create_comic_info_xml
import xml.etree.ElementTree as ET


# TODO: Pack chapters as soon as they are downloaded
# TODO: Fix Zip Output
def zip_chapter(input_dir:Path, output_dir:Path, comic:Comic, chapter:Chapter):
    files = list_files_abs(input_dir)
    output = Path(output_dir / comic.name / f"{comic.name} Vol.01 Ch.{chapter.slug.split('-')[1]}.cbz")
    if os.path.exists(output):
        os.remove(output)
    zip_files(files,output )


def download(url, output_dir, filename=None, overwrite:bool=False):
    if filename is None:
        filename = url.split('/')[-1].split('?')[0]
    if os.path.exists(filename) and not overwrite:
        return
    r = requests.get(url)
    with open(output_dir / filename, "wb") as f:
        f.write(r.content)


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


def download_chapter(comic:Comic, chapter:Chapter, output_dir:Path, library_dir:Path):
    # Download cover.jpg
    out = output_dir / "comics" / comic.slug / chapter.slug
    os.makedirs(out, exist_ok=True)

    download(comic.thumbnail_url, out, filename="cover.jpg")

    # Generate ComicXML
    generate_comic_xml(comic, chapter, out)

    urls = chapter.pages
    for url in urls:
        # print("Downloading ", url)
        download(url, out)
    
    zip_chapter(out, library_dir, comic, chapter)
