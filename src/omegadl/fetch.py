import requests
import json
import random
import datetime
import os
from utils import slugify
from pathlib import Path
from store import get_comic_by_name

def read_cookies() -> dict:
    try:
        with open("cookies.json", "r") as f:
            cookies = json.loads(f.read())
    except Exception as a:
        print("Could not read cookies")
        raise a
    return cookies


def generate_random_headers():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    ]
    
    languages = ['en-US,en;q=0.9', 'fr-FR,fr;q=0.8,en-US;q=0.7,en;q=0.6', 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7', 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7']
    
    platforms = ['"Windows"', '"macOS"', '"Linux"', '"iOS"', '"Android"']
        
    ua = random.choice(user_agents)
    lang = random.choice(languages)
    platform = random.choice(platforms)
    origin = "https://omegascans.org"
    
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-language': lang,
        'origin': origin,
        'priority': 'u=1, i',
        'referer': f'{origin}/',
        'sec-ch-ua': f'"Chromium";v="{random.randint(80, 130)}", "Not=A?Brand";v="{random.randint(1, 24)}"',
        'sec-ch-ua-mobile': f'?{random.randint(0, 1)}',
        'sec-ch-ua-platform': platform,
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': ua
    }


def _fetch(search_url:str, dump:bool, output_dir:Path=None) -> dict:
    dump_dir = output_dir / "cache" / "requests"
    resp = None
    sc = 0

    if dump:
        os.makedirs(dump_dir, exist_ok=True)
        try:
            with open(dump_dir / (slugify(search_url)+".txt"), "r") as f:
                resp = f.read()
                sc = 200
            print("Fetched request cache")
        except:
            pass

    if resp is None:
        response = requests.get(search_url, headers=generate_random_headers(), cookies=read_cookies())
        sc = response.status_code
        resp = response.text
        if dump:
            with open(dump_dir / (slugify(search_url)+".txt"), "w") as f:
                f.write(resp)
            print("Dumped request cache")
    
    if sc == 200:
        try:
            response_dict = json.loads(resp)            
        except json.JSONDecodeError:
            print("Failed to decode JSON. The response might not be in JSON format.")
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(f"Response content: \n{resp}")
    
    return response_dict


def pages(comic_dict:dict, chapter_dict:dict, output_dir:Path=None):
    print(f"Fetching {comic_dict['name']} - {chapter_dict['name']}")
    try:
        resp = _fetch(f"https://api.omegascans.org/chapter/{comic_dict['slug']}/{chapter_dict["slug"]}", dump=True, output_dir=output_dir)
        chapter_dict["data"] = resp["chapter"]["chapter_data"]["images"]
    except KeyError:
        chapter_dict["data"]= []

    return chapter_dict

def chapters(comic_dict:dict, output_dir:Path=None):
    resp = _fetch(f"https://api.omegascans.org/chapter/query?page=1&perPage=1999&series_id={comic_dict['id']}", dump=True, output_dir=output_dir)["data"]
    
    comic_dict["chapters"] = []
    for i in resp:
        chapter_dict = {
            "id": i["id"],
            "name": i["chapter_name"],
            "thumbnail_url": i["chapter_thumbnail"],
            "slug": i["chapter_slug"]
        }
        chapter_dict = pages(comic_dict, chapter_dict, output_dir)

        comic_dict['chapters'].append(chapter_dict)
    return comic_dict


def update_comics_data(output_dir:Path, response_dict: dict):
    fetched_data = {
            "meta": {
                "fetched":str(datetime.datetime.now())
            },
            "data": []
        }
    for i in response_dict:
        if i["series_type"] != "Comic":
            continue
        comic_dict = {
                "name": i["title"],
                "id": i["id"],
                "slug": i["series_slug"],
                "thumbnail_url":i["thumbnail"],
                "status":i["status"].lower(),
                "created_at": i["created_at"],
                "updated_at": i["updated_at"],
                "chapters":[]
            }
        
        comic_dict = chapters(comic_dict, output_dir)
        
        fetched_data["data"].append(comic_dict)
    
    # dump master.json
    with open(output_dir / "master.json", "w") as f:
        f.write(json.dumps(fetched_data, indent=2))


def get_chapter_pages(output_dir:Path, comic:dict, chapter:dict) -> list:
    """
    Get all image urls of pages of a particular chapter of a comic.
    #   output_dir: Ouput Directory
    #   comic: 
    #   chapter:
    """

    request_url = f"https://api.omegascans.org/chapter/{comic['slug']}/{chapter["slug"]}"
    reponse = _fetch(request_url, dump=True, output_dir=output_dir)

    return reponse["chapter"]["chapter_data"]["images"]


def get_comic_list(output_dir:Path) -> list:
    """
    Get all the comics along with their basic metadata from omegascans.
    output_dir: Pass in the output directory for omegadl
    """

    current_page = 1
    last_page = 100
    search_url = f"https://api.omegascans.org/query?adult=true"
    data = []
    
    while current_page<=last_page:
        response = _fetch(search_url, dump=True, output_dir=output_dir)
        data.extend(response["data"])

        if current_page==1:
            print("Total comics found: ", response["meta"]["total"])
            last_page = int(response["meta"]["last_page"])
        else:
            print("Fetched page ", current_page) 

        current_page +=1
        search_url= search_url.split("page=")[0] + f"page={current_page}"
    
    comic_list = []
    
    for i in data:
        if i["series_type"] != "Comic":
            continue
        comic_dict = {
                "name": i["title"],
                "id": i["id"],
                "slug": i["series_slug"],
                "thumbnail_url":i["thumbnail"],
                "status":i["status"].lower(),
                "created_at": i["created_at"],
                "updated_at": i["updated_at"],
                "chapters":[]
            }
        
        comic_dict = chapters(comic_dict, output_dir)
        
        comic_list.append(comic_dict)
    
    return comic_list


def get_chapter_list(output_dir:Path, comic:dict) -> list:
    """
    Returns the list of chapters for a given comic
    #   output_dir: Location of the output directory
    #   comic: The comic dictionary object 
    """

    request_url = f"https://api.omegascans.org/chapter/query?page=1&perPage=1999&series_id={comic['id']}"
    response: list = _fetch(request_url, dump=True, output_dir=output_dir)["data"]
    
    chapter_list = []
    for i in response:
        chapter_list.append({
            "id": i["id"],
            "name": i["chapter_name"],
            "thumbnail_url": i["chapter_thumbnail"],
            "slug": i["chapter_slug"]
        })
    
    return chapter_list


def get_chapters(output_dir:Path, comic:dict, update:bool) -> list:
    
    chapter_list = get_chapter_list(output_dir, comic)
    page_fetch_queue = []
    if update:
        for remote_chapter in chapter_list:
            for local_chapter in comic["chapters"]:
                if remote_chapter["slug"] != local_chapter["slug"]:
                    page_fetch_queue.append(remote_chapter)
    else:
        page_fetch_queue = chapter_list
    
    ordered_chapter_list = []
    
    for chapter in remote_chapter:
        if chapter in page_fetch_queue:
            pages = get_chapter_pages(output_dir, comic, chapter)
            chapter["data"] = pages
            ordered_chapter_list.append(chapter)
        else:
            for i in comic["chapters"]:
                if remote_chapter["slug"] == i["slug"]:
                    ordered_chapter_list.append(i)

    return ordered_chapter_list


def get_catalog(output_dir:Path):
    """
    Creates a catalog by fetching data from omegascans.
    Updates the catalog if output_dir contains 'catalog.json'
    output_dir: Pass in the output directory for omegadl
    """

    remote = None
    origin = None

    if os.path.exists(output_dir / "catalog.json"):
        update = True
    else:
        update = False
    
    remote = get_comic_list(output_dir)

    if update:
        origin = load_store(output_dir)
        new_list = []
        update_list = []

        # Compare Titles and Update
        for remote_comic in remote:
            local_comic = get_comic_by_name(origin, remote_comic["title"])

            if local_comic is None:
                new_list.append(remote_comic)
                continue

            if local_comic["status"].lower() == "ongoing" and remote_comic["status"].lower() == "ongoing":
                update_list.append(remote_comic)

            elif local_comic["status"].lower() == "ongoing" and remote_comic["status"].lower() != "ongoing":
                update_list.append(remote_comic)
        
        remote = new_list


def comics(output_dir:Path, query:str=None):
    current_page = 1
    last_page = 100
    search_url = f"https://api.omegascans.org/query?adult=true"
    data = []

    if query:
        search_url += f"&query_string={query}"
    search_url += "&page=1"
    
    while current_page<=last_page:
        response = _fetch(search_url, dump=True, output_dir=output_dir)
        data.extend(response["data"])

        if current_page==1:
            print("Total comics found: ", response["meta"]["total"])
            last_page = int(response["meta"]["last_page"])
        else:
            print("Fetched page ", current_page) 

        current_page +=1
        search_url= search_url.split("page=")[0] + f"page={current_page}"
    
    if query is None:
        update_comics_data(output_dir, data)
        

def load_store(output_dir:Path) -> dict:
    master_json_path = output_dir / "master.json"
    
    with open(master_json_path, "r") as f:
        comic_store = json.loads(f.read())["data"]

    return comic_store

