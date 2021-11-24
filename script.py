#! ./env/bin/python

import re
import csv
import requests
from bs4 import BeautifulSoup


BASE_URL = 'https://books.toscrape.com'


def get_product_infos(product_page_url):
    product_information = {}

    # fetch HTML page
    response = requests.get(product_page_url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')

    # extract data from the table
    table_rows = soup.select_one('.product_page .table').find_all('tr')
    pcount_regex = re.compile(r'\d+')
    for tr in table_rows:
        row_title = tr.th.string
        row_value = tr.td.string

        if row_title == 'UPC':
            product_information['universal_ product_code'] = row_value
        elif row_title == 'Price (excl. tax)':
            product_information['price_excluding_tax'] = row_value
        elif row_title == 'Price (incl. tax)':
            product_information['price_including_tax'] = row_value
        elif row_title == 'Availability':
            product_information['number_available'] = int(pcount_regex.search(
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


def get_category_products_url(category_url):
    products_url = []

    url = category_url
    while url:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        page_urls = [BASE_URL + '/catalogue/' + article.h3.a['href']
                     .lstrip('../') for article in soup.select('.product_pod')]

        products_url += page_urls
        next = soup.select_one('.next')
        if not next:
            break
        url = category_url + '/' + next.a['href']

    return products_url


def get_site_categories_url(base_url=BASE_URL):
    response = requests.get(base_url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')
    category_links = [BASE_URL + '/' + a['href'].rstrip('/index.html')
                      for a in soup.select('.side_categories .nav-list ul a')]

    return category_links


# prepare CSV file
output_file = open('report.csv', 'w')
output_dict_writer = csv.DictWriter(output_file, ['universal_ product_code', 'price_excluding_tax', 'price_including_tax',
                                    'number_available', 'product_page_url', 'title', 'description', 'image_url', 'review_rating', 'category'])
output_dict_writer.writeheader()

# retrieve data
categories_url = get_site_categories_url()
for category_page_url in categories_url:
    # print(f'Index product from category {category_page_url}')
    products_url = get_category_products_url(
        category_page_url)

    for product_page_url in products_url:
        # print(f'\tRetrieving data from product {product_page_url}')
        product_information = get_product_infos(product_page_url)
        output_dict_writer.writerow(product_information)

# byebye
output_file.close()
