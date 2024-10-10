from enum import Enum
from datetime import datetime
import json

class ComicStatus(Enum):
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    HIATUS = 'hiatus'
    DROPPED = 'dropped'

class Chapter:
    def __init__(self, name, id, slug, thumbnail_url, created_at):
        self.name = name
        self.id = id
        self.slug = slug
        self.thumbnail_url = thumbnail_url
        self.created_at= created_at

        self.pages:list[str] = []

class Comic:
    def __init__(self, name:str, id:str, slug:str, status:ComicStatus, 
                 created_at:str, updated_at:str, thumbnail_url:str):
        self.name = name
        self.id = id
        self.slug = slug
        self.status = status
        self.updated_at = updated_at
        self.created_at = created_at
        self.thumbnail_url = thumbnail_url

        self.is_subscribed:bool = False
        self.chapters:list[Chapter] = []

def dict_to_comic(comic_dict:dict) -> Comic:
    if "name" in comic_dict:
        name = comic_dict["name"]
    else:
        name = comic_dict["title"]
    id = comic_dict["id"]

    if "series_slug" in comic_dict:
        slug = comic_dict["series_slug"]
    else:
        slug = comic_dict["slug"]

    status = ComicStatus(comic_dict["status"].lower())
    updated_at = comic_dict["updated_at"]
    created_at = comic_dict["created_at"]

    if "thumbnail_url" in comic_dict:
        thumbnail_url = comic_dict["thumbnail_url"]
    else:
        thumbnail_url = comic_dict["thumbnail"]
    
    comic_obj = Comic(name=name, id=id, slug=slug, status=status, created_at=created_at, 
                updated_at=updated_at, thumbnail_url=thumbnail_url)
    
    if "chapters" in comic_dict:
        chapters = [dict_to_chapter(x) for x in comic_dict["chapters"]]
        comic_obj.chapters = chapters

    return comic_obj


def dict_to_chapter(chapter_dict:dict) -> Chapter:

    if "chapter_name" in chapter_dict:
        name = chapter_dict["chapter_name"]
    else:
        name = chapter_dict["name"]

    if "chapter_slug" in chapter_dict:
        slug = chapter_dict["chapter_slug"]
    else:
        slug = chapter_dict["slug"]

    thumbnail_url = chapter_dict["chapter_thumbnail"] if "chapter_thumbnail" in chapter_dict else chapter_dict["thumbnail_url"]

    chapter_obj = Chapter(id=chapter_dict["id"], name=name, thumbnail_url=thumbnail_url, slug=slug,created_at=chapter_dict["created_at"])

    if "pages" in chapter_dict:
        chapter_obj.pages = chapter_dict["pages"]

    return chapter_obj