import json

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
    return data


def main():
    url = 'https://www.hoppe.com/gb-en/product/amsterdam-handle-sets-for-interior-doors-1001192940-1001192940/'
    getData(url)


if __name__ == '__main__':
    main()
