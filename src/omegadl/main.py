"""
This is deprecated. Please make use of clickscript instead.
"""

import os
import sys
from pathlib import Path
import getopt
import logging
from rich.logging import RichHandler

from fetch import load_store, get_catalog
from downloader import download_chapter, zip_chapter
from catalog import load_catalog


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")


# TODO: Add comicInfo.xml stuff
# TODO: Use a logger
# TODO: Make cache optional
# TODO: Use a proper CLI framework


def view_catalog(catalog_data:dict, output_dir:Path):
    os.system("clear")
    print(f"Catalog json at: {output_dir}/catalog.json")
    print(f"Last Updated at: {catalog_data['meta']['fetched']}")

    choice = input("Would you like to update catalog (y/n): ")
    if choice == "y":
        log.info("Updating catalog...")
        get_catalog(output_dir, update=True)
        log.info("Done Updating catalog...")



def view_comic(comic_dict):
    os.system("clear")
    print("Selected comic: ", comic_dict['name'])

    print("\nCreated at: ", comic_dict['created_at'])
    print("Updated at: ", comic_dict['updated_at'])
    print("Total Chapters: ", len(comic_dict['chapters']))
    print("\n1. View Chapters")
    print("2. Go Back")

    sel = input("\nEnter your choice: ")

    if sel==2:
        return
    
    os.system("clear")
    print("Selected comic: ", comic_dict['name'])
    print(f"Location: mdlout/comics/{comic_dict['slug']}")

    try:
        files = os.listdir(f"mdlout/comics/{comic_dict['slug']}/")
    except FileNotFoundError:
        os.makedirs(f"mdlout/comics/{comic_dict['slug']}/", exist_ok=True)
        files = []
    missing_chapters = []
    for chapter in comic_dict['chapters']:
        if chapter['slug'] in files:            
            print(f"{chapter['slug']} ............. Downloaded")
        else:
            missing_chapters.append(chapter)
            print(f"{chapter['slug']} ............. Not Downloaded")

    print("\n1. Download Missing")
    print("2. Zip Chapters")
    print("3. Download Specific Chapter")
    print("4. Zip all Chapters")
    print("5. Go Back")

    choice = int(input("\nEnter your choice: "))

    if choice == 1:
        for chapter in missing_chapters:
            print(f"Downloading {chapter['name']}")
            download_chapter(comic_dict, chapter)
    if choice == 2:
        in_c = input("Enter chapter you want to zip (chapter-slug): ")
        for i in comic_dict['chapters']:
            if i['slug'] == in_c:
                chapter = i
        os.makedirs(f"/data/manga/omega/{comic_dict['name']}",exist_ok=True)
        zip_chapter(Path(f"mdlout/comics/{comic_dict['slug']}/{in_c}"), Path(f"{comic_dict['name']}"), comic_dict, chapter)
    if choice == 3:
        chapter_slug = input("Enter the chapter slug u want to download: ")
        for chapter in comic_dict['chapters']:
            if chapter['slug'] == chapter_slug:
                download_chapter(comic_dict, chapter)
                break
    if choice==4:
        for chapter in comic_dict["chapters"]:
            os.makedirs(f"/data/manga/omega/{comic_dict['name']}",exist_ok=True)
            zip_chapter(Path(f"mdlout/comics/{comic_dict['slug']}/{chapter['slug']}"), Path(f"{comic_dict['name']}"), comic_dict, chapter)


    else:
        return


def search(store):
    os.system("clear")
    name_q = input("Enter Name: ").lower().replace(" ", "")

    sel_comic = None
    for comic in store:
        _s_title = comic['name'].lower().replace(" ", "")
        if name_q in _s_title or name_q in _s_title:
            print("Found match: ", comic['name'])
            sel_comic = comic
            break
    if sel_comic is None:
        print("Could not find a comic with the given query.")
        return
    
    c_ = input("Select this comic (Y/N)?")
    if c_.lower() == "y":
        view_comic(sel_comic)
    else:
        return

def setup_args() -> dict:
    argumentList = sys.argv[1:]
    # Options
    options = "ho:"

    # Long options
    long_options = ['Help", "output=']
    output_location = ""

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)
        
        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--Help"):
                print ("Displaying Help")
                print("-o | --Output | Set the output location for the resulting files created by omega-dl. The program creates a folder 'mdlout' in the directory specified.")
            elif currentArgument in ("-o", "--Output"):
                if os.path.exists(currentValue):
                    log.info(("Set output location to (% s)") % (currentValue))
                    output_location = Path(currentValue) / "mdlout"
                    os.makedirs(output_location, exist_ok=True)
                else:
                    log.info(f"Could not access {currentValue}")
                    exit()
        if output_location == "":
            log.info("Output location not specified. Exiting...")
            exit()

                
    except getopt.error as err:
        # output error, and return with an error code
        print (str(err)) 
        quit()    

    return output_location


def main():
    output_dir = setup_args()
    log.info(f"Loading comic store from {output_dir}")
    catalog_data,_ = load_store(output_dir)
    log.info(f"Store loaded {len(catalog_data['data'])} comics successfully")

    while True:
        print("\n\nOmega Downloader 0.1\n")
        print("1. Search Comics")
        print("2. Comic Catalog")
        print("3. Quit")
        
        choice = int(input("\nEnter your choice: "))

        if choice==1:
            search(catalog_data["data"])
        elif choice==2:
            view_catalog(catalog_data, output_dir)
        else:
            quit()

main()