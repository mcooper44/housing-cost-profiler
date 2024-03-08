import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import re
from time import sleep
import csv
from random import randint
from datetime import date
import time

# url is build from..
BASE = 'https://www.kijiji.ca'
TARGET = '/b-apartments-condos/kitchener-waterloo/apartment__condo/'
END = 'c37l1700212a29276001' # not sure what this is for - but it is essential
PAGE = 'page-'
MAIN_STR = 'https://www.kijiji.ca/b-apartments-condos/kitchener-waterloo/apartment__condo/c37l1700212a29276001'
# for testing functions for individual listings
link = 'https://www.kijiji.ca/v-apartments-condos/kitchener-waterloo/fantastic-2-bedroom-2-bathroom-for-rent-in-kitchener/1676802832'

HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'}

H_FILE = 'housing_list.csv'
PAGES = 18


@dataclass
class a_listing:
    listing_id: str
    address: str
    price: str
    unit_type: str
    bedrooms: str
    bathrooms: str
    sqft: str
    headline: str
    util_headline: str
    attrs: dict # get_l_details_dl
    perks: dict # get_l_details_h4

    def get_base_str(self):
        return  [self.listing_id, self.address,
                self.price, self.unit_type,
                self.bedrooms, self.bathrooms,
                self.sqft, self.perks.get('Agreement Type', 'N/A'),
                self.perks.get('Parking Included', 'N/A'),
                self.perks.get('Air Conditioning','N/A')]

    def get_attributes(self):
        return [self.perks.get('Agreement Type', None),
                self.perks.get('Move-In Date', None),
                self.perks.get('Parking Included', None),
                self.perks.get('Furnished', None),
                self.perks.get('Smoking Permitted', None),
                self.perks.get('Air Conditioning', None),
                self.perks.get('Pet Friendly', None)]


def get_page(url=MAIN_STR):
    '''
    make a request to get the result
    using the requests library
    '''
    print('getting page:')
    print(url)
    result = requests.get(url, headers=HEADER)
    if result.status_code != 200:
        print('no result')
        return None
    else:
        return result


def parse_result(request):
    '''
    take the result created by the requests library
    and parse it using Beautiful Soup, returning
    the soup object
    '''
    if request:
        print('result recieved - parsing data...')
        return BeautifulSoup(request.text, 'html.parser')
    else:
        raise 'No data.  Request failed.'

def test_listing(url=link):
    '''
    grab a listing and test the functions
    to parse the page and pull out the key
    features we are looking for
    '''
    page = get_page(url)
    data = parse_result(page)
    dl_features = get_l_details_dl(data)
    h4_features = get_l_details_h4(data)
    t_features = get_l_title_details(data)
    u_features = get_l_unit_type(data)
    return {'dl': dl_features,
            'h4': h4_features,
            't': t_features,
            'u': u_features,
            'data': data}


def get_l_features(data):
    '''
    extract the details from the listing and return
    two dictionaries with the title details
    and the feature set that is relevant
    '''
    dl_features = get_l_details_dl(data)
    h4_features = get_l_details_h4(data)
    t_features = get_l_title_details(data)
    u_features = get_l_unit_type(data)
    title = {**t_features, **u_features}
    listing = {**dl_features, **h4_features}
    return title, listing


def get_links(data):
    '''
    takes a BeautifulSoup parsed page of listings and
    return a list of links to individual housing rental ads
    '''
    cards = [f'listing-card-list-item-{n}' for n in range(0,40)]
    lstings = data.find_all('li', attrs={'data-testid': cards})
    links = [lstings[n].find_all('a', attrs={'data-testid': ['listing-link']})[0]['href'] for n in range(0, len(lstings))]
    print(f'parsed {len(links)} links')
    return links


def create_a_listing(lid, f, f2):
    '''
    instantiates the a_listing dataclass
    '''
    #print(f'creating a listing for {lid}')
    return a_listing(lid,f['address'],f['price'],f['unit_type'],\
                     f['bedrooms'],f['bathrooms'],f2['Size (sqft)'],\
                     f['title_str'],f['util_headline'],f, f2)


def get_l_key(link):
    '''
    parses the url and extracts the id
    that the site uses to identify the listing
    '''
    return link.split('/')[-1]


def process_links(links, csv_file='housing_list.csv', base='https://www.kijiji.ca'):
    '''
    take a list of listing links from a search
    and scrape the features from the list of listings
    and return a list of the feature objects (a_listing)
    '''
    listings = []
    for link in links:
        target = f'{base}{link}'
        key = get_l_key(target)
        print(target)
        page = get_page(target)
        data = parse_result(page)
        f, f2 = get_l_features(data)
        #print('f')
        #print(f)
        #print('f2')
        #print(f2)
        l = create_a_listing(key, f, f2)
        out = l.get_base_str() + [str(date.today())] 
        write_csv(csv_file, out)
        listings.append(l)
        #print(','.join(l.get_base_str()))
        interval = 3 + randint(1,10)
        #sleep(interval)
    return listings


def get_l_details_dl(data):
    '''
    https://stackoverflow.com/questions/32475700/using-beautifulsoup-to-extract-specific-dl-and-dd-list-elements
    Most of the headings in the listing are in dl>dt>dd
    Parking Included, Agreement Type, Move-In Date,
    Pet Friendly, Size (sqft), Furnished, Air Conditioning,
    Smoking Permitted
    '''
    d = None
    if data:
        d = data.find_all('dl')
    k, v = [], []
    for dl in d:
        for dt in dl.find_all('dt'):
            k.append(dt.text.strip())
        for dd in dl.find_all('dd'):
            v.append(dd.text.strip())
    return dict(zip(k,v))


def get_l_details_h4(data):
    '''
    Extract the listing features from the
    individual listing
    h4's list the following headings:
    Wi-Fi and More, Appliances,
    Personal Outdoor Space, Amenities
    '''
    h = None
    _struct = {}
    if data:
        h = data.select('h4') # headings
    else:
        #print('no headings')
        return None
    for h4 in h: # print the Heading
        #print(h4.text)
        heading = h4.text
        _struct[heading] = []
        ul = h4.parent.select('ul') # check the parent
        if len(ul) > 0:
            # Utilities uses SVG's in a UL
            svg = ul[0].select('svg', attrs={'aria-label': True})
            if svg: # we have labels
                try:
                    for tag in svg:
                        _struct[heading].append(tag['aria-label'])
                        #print('-', tag['aria-label'])
                except:
                    pass
            # if li are present - iterate through them
            li = ul[0].select('li')
            if li and not svg:
                for l in li:
                    if len(l) > 0:
                        _struct[heading].append(l.text)
                        #print('-', l.text)
            else:
                # just one element ul
                _struct[heading].append(ul[0].text)
                #print('-', ul[0].text)
    return _struct


def get_l_title_details(data):
    '''
    Extract the title, price, price note and address
    from the individual listing page
    '''
    details = ['price', 'util_headline',
               'title_str', 'address']
    detail_str = []
    r_price = re.compile('priceWrapper')
    r_add = re.compile('locationContainer')
    price = data.find_all('div', {'class': r_price})
    if price:
        try:
            for s in price[0]:
                detail_str.append(s.text)
        except:
            detail_str.append('price error')
    # add title string
    try:
        detail_str.append(price[0].parent.select('h1')[0].text)
    except:
        detail_str.append('title error')
    # find address
    address = data.find_all('div', {'class': r_add})
    try:
        detail_str.append(address[1].select('span')[0].text)
    except:
        detail_str.append('address error')
    # zip labels and values into a dictionary
    return dict(zip(details, detail_str))


def get_l_unit_type(data):
    '''
    Extract unit type (house, 1 bedroom etc)
    Bedrooms and # of bathrooms
    '''
    details = ['unit_type', 'bedrooms',
               'bathrooms']
    detail_str = []
    row = re.compile('unitRow')
    label = re.compile('noLabelValue')
    card = data.find_all('div', {'class':row})
    span = card[0].find_all('span', {'class': label})
    for d in span:
        detail_str.append(d.text)
    return dict(zip(details, detail_str))


def write_csv(file_name, line):
    '''
    write a line to file_name - this function
    will append a line to the file and is called
    to write out the list of strings with the listing
    feature
    '''
    with open(file_name, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(line)


def generate_url_list(n):
    '''
    generates the list of urls to page through
    and strip links out of
    the structure of the url is to append PAGE
    between TARGET and END after page 1
    '''
    u = [MAIN_STR]
    for i in range(2, n):
        p = f'{PAGE}{i}/'
        s = BASE + TARGET + p + END
        u.append(s)
    return u

def main():
    listing_file = H_FILE
    url_list = generate_url_list(PAGES)
    for url in url_list:
        print(url)
        page = get_page()
        data = parse_result(page)
        link_list = get_links(data)
        listing_objs = process_links(link_list)
        print(f'processed {len(listing_objs)} links')
        print('taking a nap for 30 seconds')
        time.sleep(10)
