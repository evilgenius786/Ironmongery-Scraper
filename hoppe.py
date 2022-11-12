import json
import os
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

fields = ["SKU", "Type", "Parent", "Name", "Price", "Categories", "Images",
          "Attribute 1 Name", "Attribute 1 Value(s)", "Attribute 1 Global", "Attribute 1 Visible",
          "Attribute 2 Name", "Attribute 2 Value(s)", "Attribute 2 Global", "Attribute 2 Visible",
          "Description"]


def getData(url):
    with open('hoppe.html') as hfile:
        soup = BeautifulSoup(hfile, 'lxml')
    js_data = json.loads(soup.find('script', {"type": 'application/ld+json', "class": "rank-math-schema"}).text)
    product = {}
    for g in js_data['@graph']:
        if g['@type'] == 'Product':
            product = g
            break
    data = {
        "SKU": product['sku'],
        "Type": "simple",
        "Name": product['name'],
        "Price": product['offers']['price'],
        "Categories": product['category'].replace('&gt;', '>'),
        "Images": soup.find('img', {'id': True, 'src': True})['src'],
        "Description": str(soup.find('div', {"class": "productdetails-description-wrapper"})),
    }
    for div in soup.find_all("div", {"class": "filter-wrapper"}):
        data[div.find('div', {'class': "filter__header"}).text.strip()] = div.find('div', {
            'class': 'filter-is-selected'}).text.strip()
    for li in soup.find('div', {'id': 'tab-details'}).find_all('li'):
        litxt = li.text.strip().split(':')
        data[litxt[0].strip()] = litxt[1].strip()
    print(json.dumps(data, indent=4))
    row = {
        "SKU": data['SKU'],
        "Type": "simple",
        "Parent": "",
        "Name": data['Name'],
        "Price": data['Price'],
        "Categories": data['Categories'],
        "Images": data['Images'],
        "Attribute 1 Name": "Finish",
        "Attribute 1 Value(s)": data['Finish'],
        "Attribute 1 Global": "0",
        "Attribute 1 Visible": "1",
        "Attribute 2 Name": "Version",
        "Attribute 2 Value(s)": data['Version'],
        "Attribute 2 Global": "0",
        "Attribute 2 Visible": "1",
        "Description": data['Description'],
    }
    print(json.dumps(row, indent=4))
    return data


def processCategory(url):
    print(f"Category {url}")
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    while url:
        for div in soup.find_all('h2', {'class': 'product-name'}):
            if div.find('a'):
                href = div.find('a')['href']

                file = f"./hoppe/{href.split('/')[-2]}.html"
                if not os.path.exists(file):
                    print(f"Working on {href}")
                    res = BeautifulSoup(requests.get(href).text, 'lxml')
                    with open(file, 'w') as hfile:
                        hfile.write(res.prettify())
                else:
                    print(f"Already scraped {href}")
        page_next = soup.find('li', {"class": "pagination-next"})
        if page_next:
            page_next = page_next.find('a')
            if page_next:
                url = f"https://www.hoppe.com{page_next['href']}"
            else:
                break
        else:
            break
        print(f"Next page {url}")
        soup = BeautifulSoup(requests.get(url).text, 'lxml')


def scrapeAllProducts():
    url = 'https://www.hoppe.com/gb-en/product-catalogue/'
    # with open('hoppe-prod.html') as hfile:
    #     soup = BeautifulSoup(hfile, 'lxml')
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    x = "var wc_product_block_data = JSON.parse( decodeURIComponent( '"
    products = {}
    for line in soup.prettify().splitlines():
        if x in line:
            products = json.loads(unquote(line.replace(x, '')[:-6].strip()))
    for cat in products['productCategories']:
        processCategory(cat['link'])


def main():
    logo()
    if not os.path.exists('./hoppe'):
        os.mkdir('./hoppe')
    scrapeAllProducts()


def logo():
    print(r"""
      ___ ___                              
     /   |   \  ____ ______ ______   ____  
    /    ~    \/  _ \\____ \\____ \_/ __ \ 
    \    Y    (  <_> )  |_> >  |_> >  ___/ 
     \___|_  / \____/|   __/|   __/ \___  >
           \/        |__|   |__|        \/ 
================================================
        Hoppe Scraper by @evilgenius786
================================================
[+] Scraping all products from Hoppe
[+] CSV/JSON Output
________________________________________________
""")


if __name__ == '__main__':
    main()
