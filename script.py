#!/user/bin/env python3

import asyncio
import re
from pathlib import Path

import aiofiles
import aiohttp
from aiocsv import AsyncDictWriter
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

BASE_URL = 'https://books.toscrape.com'
IMAGE_DIRECTORY = "images"


async def fetch_html(url: str, client: ClientSession) -> str:
    """GET request wrapper to fetch HTML page at `url`."""
    response = await client.get(url)
    response.raise_for_status()

    return await response.text(encoding='utf-8')


async def fetch_product_image(url: str, client: ClientSession) -> aiohttp.ClientResponse:
    """GET request wrapper to fetch image at `url`"""
    response = await client.get(url)
    response.raise_for_status()
    return response


async def crawl_product(product_page_url: str, **kwargs) -> dict:
    """Extract product information from `product_page_url`."""
    html = await fetch_html(product_page_url, **kwargs)

    soup = BeautifulSoup(html, 'html.parser')

    product_information = {}
    # extract data from the table
    table_rows = soup.select_one('.product_page .table').find_all('tr')
    p_count_re = re.compile(r'\d+')
    for tr in table_rows:
        row_title = tr.th.string
        row_value = tr.td.string

        if row_title == 'UPC':
            product_information['universal_product_code'] = row_value
        elif row_title == 'Price (excl. tax)':
            product_information['price_excluding_tax'] = row_value
        elif row_title == 'Price (incl. tax)':
            product_information['price_including_tax'] = row_value
        elif row_title == 'Availability':
            product_information['number_available'] = int(p_count_re.search(
                row_value).group())

    # extract remainder data
    product_information['product_page_url'] = product_page_url
    product_information['title'] = soup.find('h1').string

    try:
        product_information['description'] = soup.select_one(
            '#product_description + p').string
    except AttributeError:
        # some books have no description
        product_information['description'] = ''

    product_information['image_url'] = BASE_URL + '/' + \
                                       soup.select_one('.thumbnail img')['src'].lstrip('../')

    ratings_map = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    product_information['review_rating'] = ratings_map[
        soup.select_one('.star-rating')['class'][1]]

    breadcrumb_ul = soup.select_one('.breadcrumb').find_all('li')
    product_information['category'] = breadcrumb_ul[2].a.string

    return product_information


async def process_product(product_page_url: str, dict_writer: AsyncDictWriter, lock: asyncio.locks.Lock,
                          target_dir: str,
                          **kwargs) -> None:
    """Find product information from `product_page_url` and save it to a CSV file. Download associated image."""
    product_information = await crawl_product(product_page_url, **kwargs)

    product_image = await fetch_product_image(product_information['image_url'], **kwargs)
    file_extension = '.' + product_image.content_type.lstrip('image/')
    image_name = product_information['category'].lower().replace(' ', '_') + '_' + product_information[
        'universal_product_code'] + file_extension
    async with aiofiles.open(Path(target_dir) / IMAGE_DIRECTORY / image_name, mode='wb') as image_file:
        await image_file.write(await product_image.read())

    async with lock:
        await dict_writer.writerow(product_information)


async def crawl_category(category_page_url: str, **kwargs) -> list:
    """Find products of a category from `category_page_url`."""
    products_urls = []

    url = category_page_url
    while url:
        html = await fetch_html(url, **kwargs)

        soup = BeautifulSoup(html, 'html.parser')
        page_urls = [BASE_URL + '/catalogue/' + article.h3.a['href']
            .lstrip('../') for article in soup.select('.product_pod')]

        products_urls += page_urls
        next_page_url = soup.select_one('.next')
        if not next_page_url:
            break
        url = category_page_url + '/' + next_page_url.a['href']

    return products_urls


async def process_category(category_name: str, category_page_url: str, target_dir: str, pbar: tqdm, **kwargs) -> None:
    """Find products of a category, concurrently process those to write data to a CSV file in `target_dir`."""
    lock = asyncio.Lock()
    async with aiofiles.open(Path(target_dir) / f'{category_name}.csv', mode='w', encoding='utf-8', newline='') as afp:
        dict_writer = AsyncDictWriter(afp, ['universal_product_code', 'price_excluding_tax', 'price_including_tax',
                                            'number_available', 'product_page_url', 'title', 'description', 'image_url',
                                            'review_rating', 'category'])
        await dict_writer.writeheader()

        products_urls = await crawl_category(category_page_url, **kwargs)
        tasks = []
        for product_page_url in products_urls:
            tasks.append(process_product(product_page_url, dict_writer, lock, target_dir, **kwargs))
        await asyncio.gather(*tasks)
    pbar.update(1)


async def crawl_categories_urls(home_page_url: str = BASE_URL, **kwargs) -> dict:
    """Find categories from the `home_page_url`."""
    html = await fetch_html(home_page_url, **kwargs)

    soup = BeautifulSoup(html, 'html.parser')
    categories_urls = {a.get_text(strip=True): BASE_URL + '/' + a['href'].rstrip('/index.html')
                       for a in soup.select('.side_categories .nav-list ul a')}

    return categories_urls


async def main(target_dir: str) -> None:
    """Concurrently extract data from the website's categories and write it to `target_dir`."""
    async with ClientSession() as client:
        categories_urls = await crawl_categories_urls(client=client)

        pbar = tqdm(total=len(categories_urls), ascii=True)
        tasks = []
        for category_name, category_page_url in categories_urls.items():
            tasks.append(process_category(category_name, category_page_url, target_dir, pbar, client=client))
        await asyncio.gather(*tasks)
        pbar.close()


if __name__ == '__main__':
    import sys

    assert sys.version_info >= (3, 7), f"{__file__} requires Python 3.7+"

    output_dir = sys.argv[1] if len(sys.argv) > 1 else 'report'
    Path(output_dir).mkdir(exist_ok=True)
    Path(output_dir).joinpath(IMAGE_DIRECTORY).mkdir(exist_ok=True)

    asyncio.run(main(output_dir))
