#! ./env/bin/python

import re
import csv
import pprint
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://books.toscrape.com'

output_file = open('test.csv', 'w')
output_dict_writer = csv.DictWriter(output_file, ['universal_ product_code', 'price_excluding_tax', 'price_including_tax',
                                    'number_available', 'product_page_url', 'title', 'description', 'image_url', 'review_rating', 'category'])
output_dict_writer.writeheader()

url = BASE_URL + '/catalogue/the-dirty-little-secrets-of-getting-your-dream-job_994'
response = requests.get(url)
response.raise_for_status()
response.encoding = 'utf-8'

product_information = {}

soup = BeautifulSoup(response.text, 'html.parser')

# Extract data from the table
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

# Extract remainder data
product_information['product_page_url'] = url
product_information['title'] = soup.find('h1').string
product_information['description'] = soup.select_one(
    '#product_description + p').string
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

output_dict_writer.writerow(product_information)


output_file.close()
