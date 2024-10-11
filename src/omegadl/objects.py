from enum import Enum
from pathlib import Path
import os

class ComicStatus(Enum):
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    HIATUS = 'hiatus'
    DROPPED = 'dropped'

class BreakPointOperators(Enum):
    ADD = 'add'
    DELTE = 'delete'
    MODIFY = 'modify'

class Chapter:
    def __init__(self, name, id, slug, thumbnail_url, created_at=None):
        self.name = name
        self.id = id
        self.slug = slug
        self.thumbnail_url = thumbnail_url
        self.created_at= created_at

        if self.slug == "epilogue":
            self.slug = "chapter-999"

        self.pages:list[str] = []
    
    def is_downloaded(self, comic,library:Path) -> bool:
        if os.path.exists(library / comic.name / f"{comic.name} Vol.01 Ch.{self.slug.split('-')[1]}.cbz"):
            return True
        return False

    def is_breakpoint(self, comic) -> bool:
        if self.slug in comic.volume_breakpoints.keys():
            return True
        return False

    
    def get_volume(self, comic) -> str:
        """
        Returns the volume a chapter belongs to in a comic.
        """

        current_volume = ""
        for chapter in comic.chapters:
            if chapter.is_breakpoint(comic):
                current_volume = comic.volume_breakpoints[chapter.slug]

            if chapter.slug == self.slug:
                break
        
        return current_volume


    def encode(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "slug": self.slug,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at,
            "pages": self.pages
        }


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

        self.volume_breakpoints:dict = {}
        # Stores a {chapter_slug:volume} pair that tells when a new volume starts.
    
    def breakpoint(self, operation:BreakPointOperators, chapter_slug:str, volume_name:str=None):
        match operation:
            case BreakPointOperators.ADD:
                self.volume_breakpoints[chapter_slug] = volume_name
            case BreakPointOperators.DELTE:
                del self.volume_breakpoints[chapter_slug]
            case BreakPointOperators.MODIFY:
                self.volume_breakpoints[chapter_slug] = volume_name


    def encode(self) -> dict:
        _chapters = [chapter.encode() for chapter in self.chapters]

        return {
            "name": self.name,
            "id": self.id,
            "slug": self.slug,
            "status": self.status.name,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
            "thumbnail_url": self.thumbnail_url,
            "is_subscribed": self.is_subscribed,
            "chapters": _chapters,
            "volume_breakpoints": self.volume_breakpoints
        }
    
    def get_last_downloaded_chapter(self, library) -> Chapter:
        for chapter in self.chapters:
            if chapter.is_downloaded(self, library):
                return chapter


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
    
    if "volume_breakpoints" in comic_dict:
        comic_obj.volume_breakpoints = comic_dict["volume_breakpoints"]

    return comic_obj


def dict_to_chapter(chapter_dict:dict) -> Chapter:
    # print(chapter_dict)

    if "chapter_name" in chapter_dict:
        name = chapter_dict["chapter_name"]
    else:
        name = chapter_dict["name"]

    if "chapter_slug" in chapter_dict:
        slug = chapter_dict["chapter_slug"]
    else:
        slug = chapter_dict["slug"]

    thumbnail_url = chapter_dict["chapter_thumbnail"] if "chapter_thumbnail" in chapter_dict else chapter_dict["thumbnail_url"]

    chapter_obj = Chapter(id=chapter_dict["id"], name=name, thumbnail_url=thumbnail_url, slug=slug)

    if "created_at" in chapter_dict:
        chapter_obj.created_at = chapter_dict["created_at"]

    if "pages" in chapter_dict:
        chapter_obj.pages = chapter_dict["pages"]

    return chapter_obj


