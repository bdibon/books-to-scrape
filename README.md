# books-to-scrape

## What it does

The goal of this projet is to crawl every category of books from the website [books-to-scrape](https://books.toscrape.com/).

The data points we are interested in for each book are:

* `product_page_url`
* `universal_product_code`
* `title`
* `price_including_tax`
* `price_excluding_tax`
* `number_available`
* `product_description`
* `category`
* `review_rating`
* `image_url`

These will be stored in a different CSV file for each category: `output_dir/Category Name.csv`. By default `output_dir=report`, it can be changed by passing an argument to the script `./script custom_dir`.

The script will also download the cover image of each book in the `output_dir/images` folder, images name will be formatted as follows `category_upc.jpeg`.

## How to run it

### Prerequisite

First you need to clone the repository `git clone git@github.com:bdibon/books-to-scrape.git`.

Note you must have Python version 3.7 minimum installed, this is because the script relies on [asyncio](https://docs.python.org/3/library/asyncio.html) to concurrently run the requests and write to the files.

### Setup a virtual env

* It is recommended to setup a virtual environment before runnning the script, in the repository folder execute `python -m venv env`
* Activate the virtual environment `source env/bin/activate`

### Install dependencies

* Use the provided `requirements.txt` file to install the dependencies with `pip install -r requirements.txt`

### Run it

`./script.py [output_dir]`

You should find a new directory (by default in the directory where the script resides) that contains a bunch of CSV files matching the different book categories of the site and an `images` folder populated with the cover of the books.
