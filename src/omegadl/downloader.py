import requests
from pathlib import Path
import json
import os
from utils import zip_files, list_files_abs

# TODO: Pack chapters as soon as they are downloaded
# TODO: Fix Zip Output
def zip_chapter(input_dir, output_dir, comic, chapter):
    files = list_files_abs(input_dir)
    output = Path(f"/data/manga/omega/{comic['name']}") / f"{comic['name']} Vol.01 Ch.{chapter['slug'].split('-')[1]}.cbz"
    if os.path.exists(output):
        os.remove(output)
    zip_files(files,output )


# TODO: Download series image
def download(url, output_dir):
    r = requests.get(url)
    with open(output_dir / url.split('/')[-1].split('?')[0], "wb") as f:
        f.write(r.content)

def download_chapter(comic:dict, chapter:dict):
    out = Path("mdlout")/ "comics" / comic['slug'] / chapter['slug']
    os.makedirs(out, exist_ok=True)
    urls = chapter['data']
    for url in urls:
        # print("Downloading ", url)
        download(url, out)
