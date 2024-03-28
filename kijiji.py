import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import re
from time import sleep
import csv
from random import randint
from datetime import date
import time
from util import process_address
from util import process_utility
from util import process_appliance
from util import process_price
from util import process_bb

# url is build from..
BASE = 'https://www.kijiji.ca'

TARGET = '/b-apartments-condos/kitchener-waterloo/apartment__condo/'
TARGET2 = '/b-apartments-condos/kitchener-waterloo/house/'
TARGET3 = '/b-apartments-condos/cambridge/'

END = 'c37l1700212a29276001' # not sure what this is for - but it is essential
END2 = 'c37l1700210'
PAGE = 'page-'

TARGETS = [(BASE,TARGET,END),
           (BASE,TARGET2,END),
           (BASE,TARGET3,END2)]

MAIN_STR = 'https://www.kijiji.ca/b-apartments-condos/kitchener-waterloo/apartment__condo/c37l1700212a29276001'
MAIN_STR2 = 'https://www.kijiji.ca/b-apartments-condos/kitchener-waterloo/house/c37l1700212a29276001'
MAIN_STR3 = BASE + TARGET3 + END2

# for testing functions for individual listings
link ='https://www.kijiji.ca/v-apartments-condos/cambridge/cambridge-1-bedroom-apartment-for-rent:/1670519580'

HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'}

H_FILE = 'housing_list.csv'
START = 2 # start for pages of listings - is always between 2 and n
PAGES = 18 # end for range of pages of listings


@dataclass
class a_listing:
    listing_id: int
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
    url: str

    def get_base_str(self):
        '''
        method for testing/validating
        '''
        return  [self.listing_id, self.address,
                self.price, self.unit_type,
                self.bedrooms, self.bathrooms,
                self.sqft, self.perks.get('Agreement Type', 'N/A'),
                self.perks.get('Parking Included', 'N/A'),
                self.perks.get('Air Conditioning','N/A')]

    def get_attributes(self):
        '''
        method for testing/validating
        '''
        return [self.perks.get('Agreement Type', None),
                self.perks.get('Move-In Date', None),
                self.perks.get('Parking Included', None),
                self.perks.get('Furnished', None),
                self.perks.get('Smoking Permitted', None),
                self.perks.get('Air Conditioning', None),
                self.perks.get('Pet Friendly', None)]

    def get_listing(self):
        '''
        return tuple of data needed
        to provision the Listing table
        listing_id -> int
        price -> float
        '''
        return (self.listing_id,
                process_bb(self.bedrooms),
                process_bb(self.bathrooms),
                process_numeric(self.sqft, 'Not Available'),
                self.perks.get('Agreement Type', 'Missing'),
                process_numeric(self.price, 'Please Contact'))

    def get_address(self):
        '''
        method to parse address will take some time
        '''
        return (self.listing_id, *process_address(self.address),
                self.unit_type, self.address)

    def get_description(self) -> tuple:
        return (self.listing_id,
                f"{self.headline}, {self.attrs.get('item_str', None)}")

    def get_url(self) -> tuple:
        return (self.listing_id, self.url)

    def get_features(self):
        return (self.listing_id,
                self.perks.get('Parking Included', -1),
                self.perks.get('Furnished', None),
                self.perks.get('Smoking Permitted', None),
                self.perks.get('Air Conditioning', None),
                self.perks.get('Pet Friendly', None))

    def get_utilities(self):
        return self.perks.get('Utilities Included', None)

    def get_amenities(self) -> list:
        return self.perks.get('Amenities', None)

    def get_appliances(self) -> list:
        return self.perks.get('Appliances', None)


def get_page(url: str):
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

def test_listing(url: str=link) -> dict:
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


def create_a_listing(lid, f, f2, url):
    '''
    instantiates the a_listing dataclass
    '''
    #print(f'creating a listing for {lid}')
    return a_listing(int(lid),f['address'],f['price'],f['unit_type'],\
                     f['bedrooms'],f['bathrooms'],f2['Size (sqft)'],\
                     f['title_str'],f['util_headline'],f, f2)


def get_l_key(link):
    '''
    parses the url and extracts the id
    that the site uses to identify the listing
    '''
    return link.split('/')[-1]


def process_links(links: list, csv_file: str='housing_list.csv',
                  base: str='https://www.kijiji.ca') -> list:
    '''
    take a list of listing urls from a search
    these urls are missing the base str which needs to be added back
    it will iterate through this list and extract the unique key and
    scrape the features from the listing at the url
    returning a list of the feature objects (a_listing)
    as well as writing listing features to a file.

    the feature objects will be leveraged to create database
    entry's downstream
    '''
    listings = []
    for link in links:
        f = None
        f2 = None
        l = None
        # get key, html and parse it
        target = f'{base}{link}'
        key = get_l_key(target) # grab unique listing key
        page = get_page(target) # get html
        data = parse_result(page) # parse with bs4
        # extract features
        try:
            f, f2 = get_l_features(data)
            l = create_a_listing(key, f, f2, target)
        except:
            print('could not extract features or create a_listing')
        if l:
            out = l.get_base_str() + [str(date.today())]
            write_csv(csv_file, out)
            listings.append(l)
            #print(','.join(l.get_base_str()))
            interval = 3 + randint(1,10)
            sleep(interval)
        else:
            print('failed write to csv: no data')
    return listings


def get_l_details_dl(data) -> dict:
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


def get_l_details_h4(data) -> dict:
    '''
    Extract the features from the
    individual listing captured in html headings
    h4's list the following features:
    Wi-Fi and More, Appliances,
    Personal Outdoor Space, Amenities,
    Utilities Included

    returns a dictionary with each heading as a key
    and a list containing the contents stripped from
    the listing
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
            try:
                svg = ul[0].select('svg', attrs={'aria-label': True})
                if svg: # we have labels
                    for tag in svg:
                        _struct[heading].append(tag['aria-label'])
                        #print('-', tag['aria-label'])
            except: # 'Additional Options'
                _struct[heading].append('Nothing')
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


def get_l_title_details(data) -> dict:
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


def get_l_unit_type(data) -> dict:
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


def write_csv(file_name: str, line: list) -> None:
    '''
    write a line to file_name - this function
    will append a line to the file and is called
    to write out the list of strings with the listing
    feature
    '''
    with open(file_name, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(line)


def generate_url_list(s: int, n: int, root: str, url_parts: tuple) -> list:
    '''
    generates the list of urls to page through
    and strip links out of
    the structure of the url is to append PAGE
    between TARGET and END after page 1
    because the url is constructed differently
    depending on the community root and url_parts
    will need to vary depending on the base starting
    url for the community we are targeting
    '''
    u = []
    base, target, end = url_parts
    if s == 2:
        u.append(root)
    for i in range(s, n):
        P = f'{PAGE}{i}/'
        s = base + target + P + end
        u.append(s)
    return u

def process_pages(url_list: list) -> None:
    '''
    operates on list of urls, fetches the html
    parses the html, trys to extract features
    and writes them to a csv file.
    '''
    for url in url_list:
        print(url)
        page = get_page(url)
        if page:
            data = parse_result(page)
            try:
                link_list = get_links(data)
                listing_objs = process_links(link_list)
                print(f'processed {len(listing_objs)} links')
            except:
                print('failed link processing')
        else:
            print('failed request')


def main(s: int=START, n: int=PAGES):
    listing_file = H_FILE
    roots = [(MAIN_STR3,TARGETS[2]),
             (MAIN_STR2,TARGETS[1]),
             (MAIN_STR,TARGETS[0])]
    for root, parts in roots:
        url_list = generate_url_list(s,n,root,parts)
        process_pages(url_list)
        print('taking a nap for 10 seconds')
        time.sleep(10)
    print('job complete')
