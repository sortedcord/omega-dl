### **Disclaimer**

> This project was built on a commission basis (I was paid for to create this) and so I may or may not maintain this project in the near future.

# Omegadl

A comic downloader and manager for comics on [Omegascans (NSFW)](https://omegascans.org). This program can download manwhas on a periodic basis and keep a track of new titles.


```sh
$ omegadl comics "query" download --chapters="chapter-4"
```

This command simple searches for a comic mathing `query` and then downloads the chapter with the slug `chapter-4`.

## Usage

You can use `omegadl --help` to see the list of commands and options you can use.

### Config

When omegadl is run for the first time, a config file is generated that stores the defaults. It is located at `/path/to/mdlout/config.json`. Using the config, you can change path to libraries, use of cache, [subscription lists](#subscription-lists), overwriting settings, etc.

You can revert to default settings by using the `reset-config` command.

```sh
$ omegadl reset-config
```

### Catalog Generation

In order to fetch comics from omegascans, you would need to create a catalog file that stores all the metadata for comic titles as well as their chapters and urls to chapter pages.

```sh
omegadl --output=/my/dir catalog generate
```

> Catalog generation can take anywhere from 20 minutes to one hour due to the number of requests it has to make from the server and also can get your ip address whitelisted. So, it might be better to initially generate your catalog from an existing catalog.
><br><br>This can be done by using the `--source=https://path/to/catalog` command. You can view a list of [available catalog sources]().

### Comic Database


### Downloading Comics

Downloading a comic is very straightforward. Be sure to setup your library path in the config or by using the `--library` option.

```sh
$ omegadl comics --library=/path/to/library "comic search query" download --chapter="chapter-5"
```

This would download the chapter with slug name `chapter-5` from omegascans. Ommitting `--chapter` from the command downloads all missing chapters.

### Subscription Lists

Since, it is not necessary to add all comics to the catalog, a subscription list feature has been implemented. It allows you to add the comics of your choice to a subscription list. Only those titles are added in the catalog, allowing for faster library updates.

```sh
# To add comic to subscription list
$ omegadl comics "comics search query" add 

# Removing a comic from subscription list
$ omegadl comics "comics search query" remove

# To update the catalog and download missing chapters from comics in subscription list all in one go
$ omegadl pull
```

The `omegadl pull` command updates the catalog and downloads all the missing chapters from the comics present in the subcription list at once, however it asks for your confirmation before downloading them. You can override this behaviour by adding a `--y` flag.

```sh
omegadl pull --y
```


## Installation

1. Clone the repository

    `git clone https://github.com/sortedcord/omega-dl.git`

2. Create a Virtual environmentand activate it

3. Build package and install dependencies

    ```sh
    pip install wheel # (in case wheel is not installed)
    python setup.py bdist_wheel sdist
    pip install .
    ```

You have now installed omegadl. You can now head over to [Usage](#usage) to see how this program can be used.




