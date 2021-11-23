import requests
from bs4 import BeautifulSoup
import pprint

BASE_URL = 'https://books.toscrape.com'

url = BASE_URL

response = requests.get(url)
response.raise_for_status()
response.encoding = 'utf-8'

soup = BeautifulSoup(response.text, 'html.parser')
category_links = [BASE_URL + '/' + a['href']
                  for a in soup.select('.side_categories .nav-list ul a')]
pprint.pprint(category_links)
