from omegadl.cli import cli
import click

@cli.group()
@click.pass_context
def catalog(ctx):
    """
    Commands related to the catalog stored by omegadl.
    """


@catalog.command()
@click.pass_context
def info(ctx):
    """
    Prints information about the comic catalog.
    """
    output=Path(ctx.obj['output'])

    log.info(f"Loading catalog from {output}/mdlout/catalog.json")
    catalog, sync_time = load_catalog(output_dir=output)

    click.echo(f"Catalog last synced at: {sync_time}")
    click.echo(f"Indexed {len(catalog)} titles.")


@catalog.command()
@click.pass_context
@click.option("--skip-overwrite", help="Do not generate a new catalog if it already exists.", is_flag=True, default=False)
def generate(ctx, skip_overwrite:bool=False):
    """
    Generates a fresh comic catalog.
    """
    output = ctx.obj['output']
    catalog_path = output / "catalog.json"

    if skip_overwrite and os.path.exists(catalog_path):
        log.info("Catalog already generated, skipping overwrite...")
        return

    with console.status("[bold green]Fetching comic list...") as status:
        comic_list = get_comic_list(output_dir=output)
        log.info(f"Fetched {len(comic_list)} comic titles")

    comics = []
    with Progress() as progress:
        fetch_comics_task = progress.add_task("[red]Downloading Comics Data...", total=len(comic_list))

        for comic in comic_list:
            progress.update(fetch_comics_task, description=f"[red]Downloading {comic.name}...")
            comic.chapters = get_chapters(output, comic, update=False)
            if comic.volume_breakpoints == {}:
                comic.volume_breakpoints = {comic.chapters[-1].slug: "1"}
            comics.append(comic)
            progress.update(fetch_comics_task, advance=1)
    
    dump_catalog(comics)      


@catalog.command()
@click.pass_context
@click.option("--generate-missing", help="Generate a new config if it does not exist", is_flag=True, default=False)
def update(ctx, generate_missing):
    """
    Selectively updates parts of the comic catalog if it already exists.
    """
    output = ctx.obj["output"]
    catalog_path = output / "catalog.json"

    if not os.path.exists(catalog_path):
        if generate_missing:
            generate(ctx)
        else:
            log.error(f"Catalog cannot be found at {catalog_path}. Exiting...")
        return
    
    origin_catalog,_ = load_catalog(output)

    with console.status("[bold green]Fetching comic list...") as status:
        remote_catalog = get_comic_list(output_dir=output)
        log.info(f"Fetched {len(remote_catalog)} comic titles")
    
    updated_catalog_list = []
    process_queue = [] 
    # Contains (Comic, bool) pair where bool tells if the comic needs to be updated or not.
    # If the bool is false, then all chapters will be fetched, if it is true then only selected chapters
    # will be fetched.

    # Compare Titles and Update
    for remote_comic in remote_catalog:
        local_comic = get_comic_by_id(origin_catalog, remote_comic.id)

        if local_comic is None:
            log.debug(f"{remote_comic.name} not present in local catalog. Adding to fetch list.")
            process_queue.append((remote_comic, False))
            continue

        local_comic:Comic = update_comic_metadata(local_comic, remote_comic)

        if local_comic.status == ComicStatus.ONGOING and remote_comic.status == ComicStatus.ONGOING:
            process_queue.append((local_comic, True))

        elif local_comic.status == ComicStatus.ONGOING and remote_comic.status != ComicStatus.ONGOING:
            log.debug(f"Adding {local_comic.name} to fetch list. Local status ongoing but remote status not ongoing")
            process_queue.append((local_comic, True))

        elif local_comic.status == ComicStatus.HIATUS and remote_comic.status != ComicStatus.HIATUS:
            log.debug(f"Adding {local_comic.name} to fetch list. Local status hiatus but remote status not hiatus")
            process_queue.append((local_comic, True))

        else:
            # If the comic doesn't need to be updated
            updated_catalog_list.append(local_comic)
    
    with Progress() as progress:
        update_comics_task = progress.add_task("[red]Downloading Comics...", total=len(process_queue))

        for i in process_queue:
            comic = i[0]
            progress.update(update_comics_task, description=f"[red]Updating {comic.name}...")
            comic.chapters = get_chapters(output, comic, update=i[1])
            if comic.volume_breakpoints == {}:
                comic.volume_breakpoints = {comic.chapters[-1].slug: "1"}
            updated_catalog_list.append(comic)
            log.info(f"Updated '{comic.name}' in catalog.")
            progress.update(update_comics_task, advance=1)


    dump_catalog(output, updated_catalog_list)
