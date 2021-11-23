import requests
from bs4 import BeautifulSoup
import pprint

BASE_URL = 'https://books.toscrape.com'
CATEGORY_URL = '/catalogue/category/books/nonfiction_13'

url = BASE_URL + CATEGORY_URL
while url:
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')
    urls = [BASE_URL + '/catalogue/' + article.h3.a['href'].lstrip('../')
            for article in soup.select('.product_pod')]
    pprint.pprint(urls)

    next = soup.select_one('.next')
    if not next:
        break
    url = BASE_URL + CATEGORY_URL + '/' + next.a['href']
