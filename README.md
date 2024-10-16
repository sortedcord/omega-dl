### Disclaimer

> This project was built on a commission basis (I was paid for to create this) and so I may or may not maintain this project in the near future.

# Omegadl

A comic downloader and manager for comics on [Omegascans (NSFW Warning!)](https://omegascans.org). This program can download manwhas on a periodic basis and keep a track of new titles.


```
$ omegadl comics "query" download --chapters="chapter-4"
```

This command simple searches for a comic mathing `query` and then downloads the chapter with the slug `chapter-4`.

## Usage

You can use `omegadl --help` to see the list of commands and options you can use.

### Config



### Catalog Generation

In order to fetch comics from omegascans, you would need to create a catalog file that stores all the metadata for comic titles as well as their chapters and urls to chapter pages.

```sh
omegadl --output=/my/dir catalog generate
```

### Comic Database


### Downloading Comics


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




