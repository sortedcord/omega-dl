import xml.etree.ElementTree as ET
from enum import Enum
from typing import List, Optional

class YesNo(Enum):
    UNKNOWN = "Unknown"
    NO = "No"
    YES = "Yes"

class Manga(Enum):
    UNKNOWN = "Unknown"
    NO = "No"
    YES = "Yes"
    YES_AND_RIGHT_TO_LEFT = "YesAndRightToLeft"

class AgeRating(Enum):
    UNKNOWN = "Unknown"
    ADULTS_ONLY_18_PLUS = "Adults Only 18+"
    EARLY_CHILDHOOD = "Early Childhood"
    EVERYONE = "Everyone"
    EVERYONE_10_PLUS = "Everyone 10+"
    G = "G"
    KIDS_TO_ADULTS = "Kids to Adults"
    M = "M"
    MA15_PLUS = "MA15+"
    MATURE_17_PLUS = "Mature 17+"
    PG = "PG"
    R18_PLUS = "R18+"
    RATING_PENDING = "Rating Pending"
    TEEN = "Teen"
    X18_PLUS = "X18+"

class ComicPageType(Enum):
    FRONT_COVER = "FrontCover"
    INNER_COVER = "InnerCover"
    ROUNDUP = "Roundup"
    STORY = "Story"
    ADVERTISEMENT = "Advertisement"
    EDITORIAL = "Editorial"
    LETTERS = "Letters"
    PREVIEW = "Preview"
    BACK_COVER = "BackCover"
    OTHER = "Other"
    DELETED = "Deleted"

class ComicPageInfo:
    def __init__(self, image: int, type: ComicPageType = ComicPageType.STORY, double_page: bool = False,
                 image_size: int = 0, key: str = "", bookmark: str = "", image_width: int = -1, image_height: int = -1):
        self.image = image
        self.type = type
        self.double_page = double_page
        self.image_size = image_size
        self.key = key
        self.bookmark = bookmark
        self.image_width = image_width
        self.image_height = image_height

class ComicInfo:
    def __init__(self):
        self.title: str = ""
        self.series: str = ""
        self.number: str = ""
        self.count: int = -1
        self.volume: int = -1
        self.alternate_series: str = ""
        self.alternate_number: str = ""
        self.alternate_count: int = -1
        self.summary: str = ""
        self.notes: str = ""
        self.year: int = -1
        self.month: int = -1
        self.day: int = -1
        self.writer: str = ""
        self.penciller: str = ""
        self.inker: str = ""
        self.colorist: str = ""
        self.letterer: str = ""
        self.cover_artist: str = ""
        self.editor: str = ""
        self.translator: str = ""
        self.publisher: str = ""
        self.imprint: str = ""
        self.genre: str = ""
        self.tags: str = ""
        self.web: str = ""
        self.page_count: int = 0
        self.language_iso: str = ""
        self.format: str = ""
        self.black_and_white: YesNo = YesNo.UNKNOWN
        self.manga: Manga = Manga.UNKNOWN
        self.characters: str = ""
        self.teams: str = ""
        self.locations: str = ""
        self.scan_information: str = ""
        self.story_arc: str = ""
        self.story_arc_number: str = ""
        self.series_group: str = ""
        self.age_rating: AgeRating = AgeRating.UNKNOWN
        self.pages: List[ComicPageInfo] = []
        self.community_rating: Optional[float] = None
        self.main_character_or_team: str = ""
        self.review: str = ""
        self.gtin: str = ""

def create_comic_info_xml(comic_info: ComicInfo) -> ET.Element:
    root = ET.Element("ComicInfo")
    
    for field, value in comic_info.__dict__.items():
        if field == "pages":
            pages_elem = ET.SubElement(root, "Pages")
            for page in value:
                page_elem = ET.SubElement(pages_elem, "Page")
                page_elem.set("Image", str(page.image))
                page_elem.set("Type", page.type.value)
                page_elem.set("DoublePage", str(page.double_page).lower())
                page_elem.set("ImageSize", str(page.image_size))
                page_elem.set("Key", page.key)
                page_elem.set("Bookmark", page.bookmark)
                page_elem.set("ImageWidth", str(page.image_width))
                page_elem.set("ImageHeight", str(page.image_height))
        elif isinstance(value, Enum):
            ET.SubElement(root, field.capitalize().replace("_", "")).text = value.value
        elif isinstance(value, (int, float)) and value != -1:
            ET.SubElement(root, field.capitalize().replace("_", "")).text = str(value)
        elif isinstance(value, str) and value:
            ET.SubElement(root, field.capitalize().replace("_", "")).text = value

    return root

def generate_comic_info_xml(comic_info: ComicInfo, filename: str):
    root = create_comic_info_xml(comic_info)
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)

# Example usage
# if __name__ == "__main__":
#     comic = ComicInfo()
#     comic.title = "Example Comic"
#     comic.series = "Example Series"
#     comic.number = "1"
#     comic.volume = 1
#     comic.summary = "This is an example comic."
#     comic.year = 2023
#     comic.writer = "John Doe"
#     comic.penciller = "Jane Smith"
#     comic.page_count = 24
#     comic.language_iso = "en"
#     comic.manga = Manga.NO
#     comic.age_rating = AgeRating.TEEN
    
#     comic.pages = [
#         ComicPageInfo(0, ComicPageType.FRONT_COVER),
#         ComicPageInfo(1, ComicPageType.STORY),
#         ComicPageInfo(2, ComicPageType.STORY),
#         ComicPageInfo(23, ComicPageType.BACK_COVER)
#     ]

    # generate_comic_info_xml(comic, "example_comic_info.xml")
    # print("XML file 'example_comic_info.xml' has been generated.")