import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import re
from time import sleep
import csv
from random import randint
from datetime import date
import time
import logging
from h_util import process_address
from h_util import process_utility
from h_util import process_item_list
from h_util import process_numeric
from h_util import process_bb
from h_util import process_yn
from database import Database

logger = logging.getLogger(__name__)
logging.basicConfig(filename='errors.log', encoding='utf-8', level=logging.INFO)

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
HDB = 'Housing.sqlite3'

START = 2 # start for pages of listings - is always between 2 and n
PAGES = 4 # end for range of pages of listings
TDATE = str(date.today())


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
        for writing out to csv
        '''
        return  [self.listing_id,
                 self.address,
                 process_numeric(self.price, 'Please Contact'),
                 self.unit_type,
                 self.perks.get('Agreement Type', 'N/A'),
                 process_bb(self.bedrooms),
                 process_bb(self.bathrooms),
                 process_numeric(self.sqft, 'Not Available'),
                 self.perks.get('Move-In Date', None),
                 process_numeric(self.perks.get('Parking Included', -1),None),
                 process_yn(self.perks.get('Furnished', None)),
                 process_yn(self.perks.get('Smoking Permitted', None)),
                 process_yn(self.perks.get('Air Conditioning', None)),
                 process_yn(self.perks.get('Pet Friendly', None)),
                 *process_utility(self.perks.get('Utilities Included', None)),
                 len(self.get_appliances())-1,
                 len(self.get_amenities())-1]

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
                f"{self.headline}")

    def get_url(self) -> tuple:
        return (self.listing_id, self.url)

    def get_features(self):
        return (self.listing_id,
                process_numeric(self.perks.get('Parking Included', -1),None),
                process_yn(self.perks.get('Furnished', None)),
                process_yn(self.perks.get('Smoking Permitted', None)),
                process_yn(self.perks.get('Air Conditioning', None)),
                process_yn(self.perks.get('Pet Friendly', None)))

    def get_utilities(self) -> tuple:
        return (self.listing_id,
                *process_utility(self.perks.get('Utilities Included', None)))

    def get_amenities(self) -> list:
        return process_item_list(self.listing_id, \
                                 self.perks.get('Amenities', None))

    def get_appliances(self) -> list:
        return process_item_list(self.listing_id, \
                                 self.perks.get('Appliances', None))

    def get_space(self) -> list:
        return process_item_list(self.listing_id, \
                                 self.perks.get('Personal Outdoor Space', None))
    def get_today(self) -> tuple:
        return (self.listing_id, TDATE)


def get_page(url: str):
    '''
    make a request to get the result
    using the requests library
    '''
    logger.info(f'get_page: getting page: {url}')
    result = requests.get(url, headers=HEADER)
    if result.status_code != 200:
        logger.error(f'get_page: no result from requests')
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
        logger.info('parse_result: result recieved - parsing data...')
        return BeautifulSoup(request.text, 'html.parser')
    else:
        logger.error('parse_result: CRITCAL FAILURE! No data. Request failed.')


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
    logger.info(f'get_links: parsed {len(links)} links')
    for l in links:
        logger.info(f'{l}')
    return links


def create_a_listing(lid, f, f2, url):
    '''
    instantiates the a_listing dataclass
    '''
    logger.debug(f'attempting to creating a listing for {lid}')
    return a_listing(int(lid),f['address'],f['price'],f['unit_type'],\
                     f['bedrooms'],f['bathrooms'],f2['Size (sqft)'],\
                     f['title_str'],f['util_headline'],f, f2, url)


def get_l_key(link):
    '''
    parses the url and extracts the id
    that the site uses to identify the listing
    '''
    return link.split('/')[-1]


def process_links(links: list, dbh, csv_file: str='housing_list.csv',
                  base: str='https://www.kijiji.ca') -> None:
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
    for link in links:
        logger.info(f'process_links: working on: {link}')
        f = None
        f2 = None
        l = None
        # get key, html and parse it
        #target = f'{base}{link}'
        target = link
        logger.debug(f'process_links: working on target: ')
        logger.debug(f'{target}')
        key = get_l_key(target) # grab unique listing key
        logger.debug(f'derived key: {key}')
        if check_key(key, dbh): # returns bool
            logger.info(f'process_links: target {key} exists.  Skipping..')
        else: # not in the db yet
            logger.debug('attempting to get page and data...')
            page = get_page(target) # get html
            data = parse_result(page) # parse with bs4
            logger.debug('page and data derived.  Sleeping...')
            sleep(4) # courtesy pause
            logger.debug('awake')
            # extract features
            try:
                logger.info('process_links: attempting to get features')
                f, f2 = get_l_features(data)
                l = create_a_listing(key, f, f2, target)
                logging.debug('process_links: features found')
            except Exception as e:
                logger.error('process_links: could not extract features or create a_listing')
                logger.error(f'key: {key}, target: {target} f:{f} f2:{f2}')
                logger.error(e)
            if l:
                out = l.get_base_str() + [TDATE]
                structure = None
                try:
                    logger.debug('trying to write to csv')
                    write_csv(csv_file, out)
                    logger.debug(f"wrote: {','.join(l.get_base_str())}")
                except Exception as e:
                    logger.error('process_links: failed to write to csv')
                    logger.error(e)
                try:
                    structure = insert_l2db(l, dbh)
                    if structure == True:
                        logger.info('process_links: already logged')
                    else:
                        logger.info('process_links: logged to db')
                except Exception as e:
                    logger.warning('process_links: failed to write to db')
                    logger.error(e)
                    logger.error(structure)
                    logger.error(l)
            else:
                logger.error('process_links: failed write to csv and database')
                logger.error('could not create listing')


def get_l_details_dl(data) -> dict:
    '''
    https://stackoverflow.com/questions/32475700/using-beautifulsoup-to-extract-specific-dl-and-dd-list-elements
    Most of the headings in the listing are in dl>dt>dd
    Parking Included, Agreement Type, Move-In Date,
    Pet Friendly, Size (sqft), Furnished, Air Conditioning,
    Smoking Permitted
    '''
    d = None
    target_keys = ['Parking Included', 'Agreement Type',
                   'Move-In Date', 'Pet Friendly', 'Size (sqft)',
                   'Furnished', 'Air Conditioning',
                   'Smoking Permitted']
    if data:
        d = data.find_all('dl')
    k, v = [], []
    for dl in d:
        for dt in dl.find_all('dt'):
            k.append(dt.text.strip())
        for dd in dl.find_all('dd'):
            v.append(dd.text.strip())
    collected = dict(zip(k,v))
    for tk in target_keys:
        if tk not in collected.keys():
            collected[tk] = None
    return collected


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
    collected = {}
    if data:
        h = data.select('h4') # headings
    else:
        logger.debug('no headings')
        return None
    for h4 in h: # print the Heading
        logger.debug(h4.text)
        heading = h4.text
        collected[heading] = []
        ul = h4.parent.select('ul') # check the parent
        if len(ul) > 0:
            # Utilities uses SVG's in a UL
            try:
                svg = ul[0].select('svg', attrs={'aria-label': True})
                if svg: # we have labels
                    for tag in svg:
                        collected[heading].append(tag['aria-label'])
                        logger.debug(f"- {tag['aria-label']}")
            except: # 'Additional Options'
                collected[heading].append('Nothing')
            # if li are present - iterate through them
            li = ul[0].select('li')
            if li and not svg:
                for l in li:
                    if len(l) > 0:
                        collected[heading].append(l.text)
                        logger.debug(f'- {l.text}')
            else:
                # just one element ul
                collected[heading].append(ul[0].text)
                logger.debug(f'- {ul[0].text}')
    return collected


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
    '''
    In appartment or house listings price will contain
    price and utility details
    In room for rent listings it will only list
    the price.
    '''
    if price:
        try:
            price_util = [s.text for s in price[0]]
            if len(price_util) == 2:
                detail_str.extend(price_util)
            elif len(price_util) == 1:
                detail_str.extend([price_util[0],'None'])
        except:
            detail_str.append('price error')
            detail_str.append('no utility summary')
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
        detail_str.append(None)
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
    collected = dict(zip(details, detail_str))
    if not collected: # it's a sublet room
        return dict(zip(details, ['room', -1, -1]))
    else:
        return collected # house or standard apartment


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

def gen_l_struct(lo) -> dict:
    '''
    call the listing methods to format the
    features into tuples that can be inserted
    into the database then return a data structure
    with the table name, and the format elements
    needed to insert it into the database
    by calling the .insert method of the database
    which expects this structure
    '''
    l_tab = ([lo.get_listing()], '(?,?,?,?,?,?)')
    a_tab = ([lo.get_address()], '(?,?,?,?,?,?,?)')
    d_tab = ([lo.get_description()], '(?,?)')
    u_tab = ([lo.get_url()], '(?,?)')
    f_tab = ([lo.get_features()], '(?,?,?,?,?,?)')
    utl_tab = ([lo.get_utilities()], '(?,?,?,?)')
    am_tab = ([x for x in lo.get_amenities()], '(?,?)')
    app_tab = ([x for x in lo.get_appliances()], '(?,?)')
    s_tab = ([x for x in lo.get_space()], '(?,?)')
    date_tab = ([lo.get_today()], '(?,?)')
    return {'Listing': l_tab,
            'Address': a_tab,
            'Description': d_tab,
            'url': u_tab,
            'Features': f_tab,
            'Utilities': utl_tab,
            'Amenities': am_tab,
            'Appliances': app_tab,
            'Space': s_tab,
            'Udate': date_tab}


def insert_l2db(o, db_handle) -> dict:
    '''
    insert listing into database
    place a datastructure of
    'table name': ([tuple of n data points],'(?,...n)')
    and using the db_handle.insert() method
    compose an INSERT string with 'table name'
    and VALUES '(?,...n)' and insert the n data points
    or if there is a list composed by the listing.method
    iterate through that data and insert it sequentially

    o is a listing object
    '''
    done = check_key(o.listing_id, db_handle)
    if not done:
        db_struct = gen_l_struct(o)
        db_handle.insert(db_struct, echo=False)
        return db_struct
    else:
        '''
        seen = check_key(o.listing_id, db_handle, 'Observed')
        if not seen:
            log_observed(o.listing_id, db_handle)
        '''
        return True


def log_observed(LID, db_handle):
    db_handle.insert({'Observed': ([(LID, TDATE)],'(?,?)')})


def check_key(LID, dbh, tbl='Listing') -> bool:
    sql_str = f'SELECT LID FROM {tbl} WHERE LID={LID} LIMIT 1'
    row = dbh.lookup_string(sql_str, None)
    return True if row else False


def process_pages(url_list: list, dbh=None) -> None:
    '''
    operates on list of urls, fetches the html
    parses the html, trys to extract features
    and writes them to a csv file.
    '''

    for url in url_list:
        logger.debug(f'process_pages: working on: {url}')
        logger.debug('...')
        page = get_page(url)
        if page:
            data = parse_result(page)
            logger.debug('retrieved page')
            try:
                logger.info('process_pages: getting links')
                link_list = get_links(data)
                logger.info('process_pages: link_list derived')
                '''
                 now process the links
                 - create listing objects
                 - write a summary to the csv
                 - write to the database
                '''
                process_links(link_list, dbh)
                logger.info(f'process_pages: processed {len(link_list)} links')
            except:
                logger.error('process_pages: failed link processing for:')
                logger.error(url)
        else:
            logger.error(f'process_pages: NO PAGE! failed request: {url}')


def main(s: int=START, n: int=PAGES):
    listing_file = H_FILE
    roots = [(MAIN_STR3,TARGETS[2]),
             (MAIN_STR2,TARGETS[1]),
             (MAIN_STR,TARGETS[0])]
    the_db = Database(HDB)
    the_db.connect()
    print(f'{TDATE} starting...')
    try:
        for root, parts in roots:
            print(f'processing {root}')
            url_list = generate_url_list(s,n,root,parts)
            print('begining to process pages')
            process_pages(url_list, the_db)
            logger.info(f'main: processed root: {TDATE} {root}')
            sleep(5)
    except:
        the_db.close()
    print('job complete')

if __name__ == '__main__':
    main()

