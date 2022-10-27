import csv
import json
import os
import threading

import openpyxl
import requests
from bs4 import BeautifulSoup

thread_count = 10
semaphore = threading.Semaphore(thread_count)

fields = ["SKU", "Type", "Parent", "Name", "Price", "Categories", "Images",
          "Attribute 1 Name", "Attribute 1 Value(s)", "Attribute 1 Global", "Attribute 1 Visible",
          "Attribute 2 Name", "Attribute 2 Value(s)", "Attribute 2 Global", "Attribute 2 Visible",
          "Description", "URL"]
idx = 0
encoding = 'utf8'


def getData(filename):
    global idx
    with open(filename, encoding=encoding) as f:
        soup = BeautifulSoup(f, 'html.parser')
    prod_json = soup.find('script', {"data-product-json": True})
    if not prod_json:
        print(f"Skipping {filename}")
        os.remove(filename)
        return
    product = json.loads(prod_json.text)['product']
    # print(json.dumps(script, indent=4))
    variants = product['variants']
    rows = []
    brand = "ZeroPlus"
    attribs = product['options']
    if len(variants) > 1:
        sku = f"{brand}{idx:03d}"
        idx += 1
        for variant in variants:
            row = {
                # 'URL': url,
                'SKU': variant['sku'],
                'Type': 'Simple',
                'Parent': sku,
                'Price': variant['price'],
                'Images': variant['featured_image']['src'] if variant['featured_image'] else '',
                'Attribute 1 Name': attribs[0] if len(attribs) > 0 else '',
                'Attribute 1 Value(s)': variant['option1'],
                'Attribute 1 Global': 1,
                'Attribute 1 Visible': 0,
                'Attribute 2 Name': attribs[1] if len(attribs) > 1 else '',
                'Attribute 2 Value(s)': variant['option2'],
                'Attribute 2 Global': 1,
                'Attribute 2 Visible': 0,
            }
            rows.append(row)
            # break
        row = {
            'SKU': sku,
            'Type': 'Variable',
            'Parent': "",
            'Name': product['title'],
            'Categories': product['tags'][-1],
            'Images': variants[0]['featured_image']['src'] if variants[0]['featured_image'] else '',
            'Description': product['description'],
            'Attribute 1 Name': attribs[0] if len(attribs) > 0 else '',
            'Attribute 1 Value(s)': ", ".join([v['option1'] for v in variants if v['option1']]),
            'Attribute 1 Global': 1,
            'Attribute 1 Visible': 1,
            'Attribute 2 Name': attribs[1] if len(attribs) > 1 else '',
            'Attribute 2 Value(s)': ", ".join([v['option2'] for v in variants if v['option2']]),
            'Attribute 2 Global': 1,
            'Attribute 2 Visible': 0,
            'URL': f"https://zeroplus.co.uk/products/{product['handle']}",
        }
        rows.insert(0, row)
    else:
        rows.append({
            "SKU": product['variants'][0]['sku'],
            "Type": "Simple",
            "Name": product['title'],
            "Price": product['price'],
            "Categories": product['tags'][-1],
            "Images": variants[0]['featured_image']['src'] if variants[0]['featured_image'] else "",
            'Attribute 1 Name': attribs[0] if len(attribs) > 0 else '',
            'Attribute 1 Value(s)': ", ".join([v['option1'] for v in variants if v['option1']]),
            'Attribute 1 Global': 1,
            'Attribute 1 Visible': 1,
            'Attribute 2 Name': attribs[1] if len(attribs) > 1 else '',
            'Attribute 2 Value(s)': ", ".join([v['option2'] for v in variants if v['option2']]),
            'Attribute 2 Global': 1,
            'Attribute 2 Visible': 0,
            "Description": product['description'],
            'URL': f"https://zeroplus.co.uk/products/{product['handle']}",
        })
    return rows


def download(file, link):
    with semaphore:
        print(f"Downloading {file}")
        with open(f'zeroplus/{file}.html', 'w', encoding=encoding) as f:
            f.write(requests.get(f"https://zeroplus.co.uk/{link}").text)


def scrapeListings():
    if not os.path.isdir('zeroplus'):
        os.mkdir('zeroplus')
    size = 250
    api = '6A9e3I7B3F'
    url = f'https://www.searchanise.com/getresults?api_key={api}&maxResults={size}'
    res = requests.get(url).json()
    total = res['totalItems']
    print(f"Total: {total}")
    threads = []
    for i in range(0, total, size):
        print(f"Scraping {i} to {i + size}")
        url = f'https://www.searchanise.com/getresults?api_key={api}&maxResults={size}&startIndex={i}'
        print(url)
        res = requests.get(url).json()
        for item in res['items']:
            link = item['link']
            file = link.split('/')[-1]
            if os.path.isfile(f'zeroplus/{file}.html'):
                print(f"Skipping {file}")
                continue
            t = threading.Thread(target=download, args=(file, link))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()


def main():
    logo()
    scrapeListings()
    print("Scraping listings done")
    with open('zeroplus.csv', 'w', newline='') as f:
        csv.DictWriter(f, fieldnames=fields).writeheader()
    data = []
    for file in os.listdir('zeroplus'):
        if file.endswith('.html'):
            rows = getData(f'zeroplus/{file}')
            if not rows:
                continue
            data.extend(rows)
    print("Combining products done")
    with open('zeroplus.csv', 'a', encoding=encoding, newline='') as f:
        csv.DictWriter(f, fieldnames=fields).writerows(data)
    convert('zeroplus.csv')


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


def logo():
    print(r"""
    __________                 __________.__                
    \____    /___________  ____\______   \  |  __ __  ______
      /     // __ \_  __ \/  _ \|     ___/  | |  |  \/  ___/
     /     /\  ___/|  | \(  <_> )    |   |  |_|  |  /\___ \ 
    /_______ \___  >__|   \____/|____|   |____/____//____  >
            \/   \/                                      \/ 
================================================================
        ZeroPlus.co.uk - Scraping script by @evilgenius786
================================================================
[+] Scrapes all products from ZeroPlus.co.uk
[+] API Based
[+] Resumable
[+] Cache response
[+] Generates CSV file
[+] Generates JSON file
________________________________________________________________
""")


if __name__ == '__main__':
    main()
