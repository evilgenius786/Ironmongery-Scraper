import requests
from bs4 import BeautifulSoup


def getData(url):
    with open('tradesecuritysupplies.html') as hfile:
        soup = BeautifulSoup(hfile, 'lxml')
    soup.find("tr",recursive=False)
    data = {
        "SKU":"",
        "Type": "simple",
        "Name": soup.find('meta', {"property": "og:title"}),
        "Price": product['offers']['price'],
        "Categories": product['category'].replace('&gt;', '>'),
        "Images": soup.find('img', {'id': True, 'src': True})['src'],
        "Description": soup.find('meta', {"property": "og:description"}),
    }


def main():
    url = 'https://www.tradesecuritysupplies.co.uk/multipoint-door-handle-122'
    print(getData(url))


if __name__ == '__main__':
    main()
