from omegadl.cli import cli
import click

@cli.group()
@click.pass_context
@click.argument("query")
def comics(ctx, query):
    """
    Commands related to comics. Require a catalog.
    """
    ctx.obj["query"] = query

def list_comics(catalog:list[Comic], library):
    table = Table(title="Indexed Comic Titles")

    table.add_column("Comic ID", justify="left", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Comic Status", justify="left", style="green")
    table.add_column("Comic Subscribed", justify="left", style="green")
    table.add_column("Latest Chapter", justify="left", style="green")
    table.add_column("Downloaded")

    for comic in catalog:
        if comic is None:
            continue

        last_downloaded_chapter = comic.get_last_downloaded_chapter(library)

        latest_chapter = comic.chapters[0].name

        if last_downloaded_chapter is None:
            last_downloaded_chapter = "[red]Not downloaded[/red]"
        else:
            last_downloaded_chapter = last_downloaded_chapter.name
        
        if latest_chapter == last_downloaded_chapter:
            last_downloaded_chapter = "[green][bold]Up-to-date[/bold][/green]"

        table.add_row(str(comic.id), comic.name[0:70], comic.status.name, 
                      str(comic.is_subscribed), latest_chapter, last_downloaded_chapter)

    console.print(table)

@comics.command()
@click.pass_context
def list(ctx):
    """
    Search for comics. You can search via comic id or comic name.
    """
    output = ctx.obj["output"]
    query = ctx.obj["query"]
    library = ctx.obj['library']

    catalog,_ = load_catalog(output)
    
    list_comics(search_comics(catalog, query), library)

@comics.command()
@click.pass_context
@click.option("--chapters", help="Specifiy the chapter slugs (separated by comma) you want to download. List Slicing works as well")
def download(ctx, chapters=None):
    """
    Downloads the missing chapters of a comic. Requires the chapter(s) as an option.
    """
    chapters_query = chapters
    output = ctx.obj["output"]
    query = ctx.obj["query"]
    library = ctx.obj['library']

    catalog,_ = load_catalog(output)
    comic = search_comics(catalog, query)[0]

    # Get chapters:
    download_queue = []

    # Fetch Missing Chapters
    if chapters_query is None:
        for chapter in comic.chapters:
            if not chapter.is_downloaded(comic, library):
                download_queue.append(chapter)


    # TODO: Add ability to select chapter using chapter IDs and chapter slugs both.
    else:
        download_queue = []
        for range in chapters_query.split(","):
            if ":" in range:
                # Splice range
                start,end = range.split(":")[0], range.split(":")[1]
                queue_add = False
                for chapter in comic.chapters:
                    if chapter.slug == start:
                        queue_add = True
                    elif chapter.slug == end:
                        queue_add = False
                        break
                    if queue_add:
                        download_queue.append(chapter)
            else:
                for chapter in comic.chapters:
                    if chapter.slug == range:
                        download_queue.append(chapter)
    
    with Progress() as progress:
        download_chapter_task = progress.add_task("[red]Downloading Chapters...", total=len(download_queue))

        for i,chapter in enumerate(download_queue):
            progress.update(download_chapter_task, 
                            description=f"[red][{i}/{len(download_queue)}] Downloading {chapter.name} - {comic.name[0:40]}...")
            download_chapter(comic, chapter, output, library)
            log.info(f"Downloaded {chapter.name} - {comic.name[0:40]}...")
            progress.update(download_chapter_task, advance=1)
