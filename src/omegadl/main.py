import time
import os
from fetch import load_store
from pathlib import Path
from downloader import download_chapter, zip_chapter
import getopt
import sys

# TODO: Fix up output location configurations.
# TODO: Add comicInfo.xml stuff
# TODO: Pack chapters as soon as they are downloaded
# TODO: Add comic_store updating functions
# TODO: Use a logger
# TODO: Make cache optional

def view_comic(comic_dict):
    os.system("clear")
    print("Selected comic: ", comic_dict["name"])

    print("\nCreated at: ", comic_dict['created_at'])
    print("Updated at: ", comic_dict['updated_at'])
    print("Total Chapters: ", len(comic_dict["chapters"]))
    print("\n1. View Chapters")
    print("2. Go Back")

    sel = input("\nEnter your choice: ")

    if sel==2:
        return
    
    os.system("clear")
    print("Selected comic: ", comic_dict["name"])
    print(f"Location: mdlout/comics/{comic_dict["slug"]}")

    try:
        files = os.listdir(f"mdlout/comics/{comic_dict["slug"]}/")
    except FileNotFoundError:
        os.makedirs(f"mdlout/comics/{comic_dict["slug"]}/", exist_ok=True)
        files = []
    missing_chapters = []
    for chapter in comic_dict["chapters"]:
        if chapter["slug"] in files:            
            print(f"{chapter["slug"]} ............. Downloaded")
        else:
            missing_chapters.append(chapter)
            print(f"{chapter["slug"]} ............. Not Downloaded")

    print("\n1. Download Missing")
    print("2. Zip Chapters")
    print("3. Download Specific Chapters")
    print("4. Go Back")

    choice = int(input("\nEnter your choice: "))

    if choice == 1:
        for chapter in missing_chapters:
            print(f"Downloading Chapter {chapter["name"]}")
            download_chapter(comic_dict, chapter)
    if choice == 2:
        in_c = input("Enter chapter you want to zip (chapter-slug): ")
        for i in comic_dict["chapters"]:
            if i["slug"] == in_c:
                chapter = i
        os.makedirs(f"{comic_dict["name"]}",exist_ok=True)
        zip_chapter(Path(f"mdlout/comics/{comic_dict['slug']}/{in_c}"), Path(f"{comic_dict["name"]}"), comic_dict, chapter)

    else:
        return


def search(store):
    os.system("clear")
    name_q = input("Enter Name: ").lower().replace(" ", "")

    sel_comic = None
    for comic in store:
        _s_title = comic["name"].lower().replace(" ", "")
        if name_q in _s_title or name_q in _s_title:
            print("Found match: ", comic["name"])
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
    long_options = ["Help", "output="]
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
                    print (("[omegadl] Set output location to (% s)") % (currentValue))
                    output_location = Path(currentValue) / "mdlout"
                    os.makedirs(output_location, exist_ok=True)
                else:
                    print("[omegadl] Could not access ", currentValue)
                    exit()
        if output_location == "":
            print("[omegadl] Output location not specified. Exiting...")
            exit()

                
    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))     

    return output_location


def main():
    output_dir = setup_args()
    store = load_store(output_dir)
    print("[Omegadl] Store loaded successfully")

    while True:
        print("\n\nOmega Downloader 0.1\n")
        print("1. Search Comics")
        print("2. Quit")
        
        choice = int(input("\nEnter your choice: "))

        if choice==1:
            search(store)
        elif choice==2:
            quit()

main()