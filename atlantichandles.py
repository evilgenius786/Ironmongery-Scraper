import csv
import json
import os
import threading
import traceback

import openpyxl
import requests
from bs4 import BeautifulSoup

fields = ["SKU", "Type", "Parent", "Name", "Price", "Categories", "Images",
          "Attribute 1 Name", "Attribute 1 Value(s)", "Attribute 1 Global", "Attribute 1 Visible",
          "Attribute 2 Name", "Attribute 2 Value(s)", "Attribute 2 Global", "Attribute 2 Visible",
          "Description"]
thread_count = 10
semaphore = threading.Semaphore(thread_count)
encoding = "utf8"


def getData(file):
    if not os.path.isfile(file):
        soup = getSoup(f"https://atlantichandles.com/products/{file.split('/')[-1].split('.')[0]}")
    else:
        with open(file, 'r', encoding=encoding) as f:
            soup = BeautifulSoup(f.read(), 'lxml')
    print(f"Scraping {soup.title.text.strip()}")
    script = json.loads(soup.find('script', {'type': 'application/ld+json'}).text)
    name = soup.find('h1').text.strip()
    desc = ""
    if soup.find('div', {'class': 'woocommerce-product-details__short-description'}):
        desc = soup.find('div', {'class': 'woocommerce-product-details__short-description'}).text.strip()
    if soup.find('div', {'id': 'tab-description'}):
        desc += soup.find('div', {'id': 'tab-description'}).text.strip()
    table_res = soup.find('div', {'class': 'dnd-data table-responsive'})
    if table_res and table_res.find('p'):
        name = table_res.find('p').text.strip()
    sku = soup.find('span', {'class': 'sku'}).text.strip() if soup.find('span', {'class': 'sku'}) else name.split()[0]
    sku = sku.split()[0]
    if "@graph" in script:
        for graph in script['@graph']:
            if graph['@type'] == 'Product':
                if name == "":
                    name = graph['name']
                # desc = "\n".join([x for x in graph['description'].split("\n")[1:] if x.strip()])
                if len(name.split()) == 1 and graph['name'] != "":
                    name = graph['description'].split("\n")[0]
                desc = "\n".join([x for x in graph['description'].split("\n")[1:]])
                if "\nRange" in desc:
                    desc = desc.split("\nRange")[0].strip()
                if desc.startswith('Range'):
                    desc = desc.split("Range")[1].strip()
                break
    data = {
        "SKU": sku,
        "Type": "Simple",
        "Name": name,
        # "Price": product['offers']['price'],  # need to login
        "Categories": soup.find('span', {"class": "posted_in"}).find('a').text.strip(),
        "Images": soup.find('a', {"data-elementor-open-lightbox": "no", "href": True})['href'],
        "Description": desc.strip(),
    }
    for table in soup.find_all('table'):
        ths = table.find_all('th')
        tds = table.find_all('td')
        for th, td in zip(ths, tds):
            data[th.text.strip()] = td.text.strip()

    row = {
        "SKU": data["SKU"],
        "Type": data["Type"],
        "Parent": "",
        "Name": data["Name"],
        "Price": data["Price"] if "Price" in data else "",
        "Categories": data["Category"] if "Category" in data else data["Categories"],
        "Images": data["Images"],
        "Attribute 1 Name": "Size",
        "Attribute 1 Value(s)": data["Size"] if "Size" in data else "",
        "Attribute 1 Global": 0,
        "Attribute 1 Visible": 1,
        "Attribute 2 Name": "Finish",
        "Attribute 2 Value(s)": data["Finish"] if "Finish" in data else "",
        "Attribute 2 Global": 0,
        "Attribute 2 Visible": 1,
        "Description": data["Description"],
    }
    # print(json.dumps(data, indent=4))
    # print(json.dumps(row, indent=4))
    return row


def main():
    # getData("./atalantichandles/AHCHAB.html")
    # exit()
    logo()
    if not os.path.isdir('atalantichandles'):
        os.mkdir('atalantichandles')
    scrapeAllProducts()
    with open('atalantichandles.csv', 'w', encoding=encoding, newline='') as f:
        csv.DictWriter(f, fields).writeheader()
    for file in os.listdir('atalantichandles'):
        try:
            row = getData(f'atalantichandles/{file}')
            with open('atalantichandles.csv', 'a', encoding=encoding, newline='') as f:
                csv.DictWriter(f, fields).writerow(row)
            # break
        except:
            print(f"Error in {file}")
            traceback.print_exc()
            input("Press enter to continue")
    convert('atalantichandles.csv')


def downloadPage(url):
    with semaphore:
        file = f"./atalantichandles/{url.split('/')[-2]}.html"
        if os.path.isfile(file):
            print(f"Skipping {url}")
            return
        print(f"Downloading {url}")
        res = getSoup(url).prettify()
        with open(file, 'w', encoding=encoding) as f:
            f.write(res)


def convert(filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    count = 0
    with open(filename, encoding=encoding) as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            ws.append(row)
            count += 1
    if count > 1:
        wb.save(filename.replace("csv", "xlsx"))
    else:
        os.remove(filename)


def scrapeAllProducts():
    per_page = 48
    url = "https://atlantichandles.com/products"
    soup = getSoup(url)
    count = soup.find('p', {'class': 'woocommerce-result-count'}).text.strip().split()[-2]
    print(f"Found {count} products")
    threads = []
    for page in range(1, int(count) // per_page + 2):
        print(f"Scraping page {page}")
        soup = getSoup(f"{url}/page/{page}/?per_page={per_page}")
        for link in soup.find_all('a', {'class': 'open-quick-view quick-view-button'}):
            t = threading.Thread(target=downloadPage, args=(link['href'],))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()


def getSoup(url):
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
         '(KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    return BeautifulSoup(requests.get(url, headers={'user-agent': ua}).text, 'lxml')


def logo():
    print(r"""
   _____   __  .__                 __  .__         ___ ___                    .___.__                 
  /  _  \_/  |_|  | _____    _____/  |_|__| ____  /   |   \_____    ____    __| _/|  |   ____   ______
 /  /_\  \   __\  | \__  \  /    \   __\  |/ ___\/    ~    \__  \  /    \  / __ | |  | _/ __ \ /  ___/
/    |    \  | |  |__/ __ \|   |  \  | |  \  \___\    Y    // __ \|   |  \/ /_/ | |  |_\  ___/ \___ \ 
\____|__  /__| |____(____  /___|  /__| |__|\___  >\___|_  /(____  /___|  /\____ | |____/\___  >____  >
        \/               \/     \/             \/       \/      \/     \/      \/           \/     \/ 
=======================================================================================================
            Atlantic Handles - https://atlantichandles.com scraper by @evilgenius786
=======================================================================================================
[+] Scraping all products
[+] Resumable
_______________________________________________________________________________________________________
""")


if __name__ == '__main__':
    main()
