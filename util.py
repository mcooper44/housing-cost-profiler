from ez_address_parser import AddressParser
from typing import Union

def process_ap(lst: list, lbl: str, max_rep: int=2):
    '''
    take an ez-address-parser list and a specific
    label and return a string made of up those elements
    e.g. postal code, municipality
    '''
    r = []
    for t in lst:
        v,l = t
        if l == lbl:
            if len(r) < max_rep:
                r.append(v)
    return ' '.join(r) if r else None

def get_sa(lst: list) -> Union[str, None]:
    '''
    get street address
    call process_ap with a list of street
    address labels to recompose the street address
    into a distinct string for logging in the dbase
    '''

    ls = ['StreetNumber', 'StreetName', 'StreetType',
          'StreetDirection']
    s = []
    for v in ls:
        t = process_ap(lst, v)
        if t:
            s.append(t)
    return ' '.join(s) if s else None


def process_address(address: list) -> tuple:
    '''
    leverage ez-address-parser to process the address string
    into labelled (element, label pairs)

    call the helper functions process_ap and get_sa to separate
    out the elements needed for the database

    return a list of (street string, city string, postal code string)
    to facilitate db insertion
    '''
    ap = AddressParser()
    t = ap.parse(address)
    city = process_ap(t, 'Municipality', 1)
    pcode = process_ap(t, 'PostalCode')
    prov = process_ap(t, 'Province', 1)
    street = get_sa(t)
    return (street, city, prov, pcode)


def process_utility(utility: list) -> tuple:
    '''
    recieves the 'Utilities Included'
    output from a_listing method which is a list
    and returns a dictionary keyed by utility
    Utilities Included is in the h4 tags in the listing
    which returns a list
    an example of input is:
    ['No: Hydro', 'Yes: Heat', 'Yes: Water','HydroHeatWater']
    as the function lumps the headings into one str we want
    to avoid the last value
    and convert the yes' to 1 and no to 0 and errors to -1
    returns a tuple so that these values can be integrated
    into a db insertion
    '''
    d = {}
    lu = {'No': 0, 'Yes': 1}
    for utl in utility:
        v = utl.split(':')
        if len(v) == 2:
            d[v[1].strip()] = lu.get(v[0], -1)
    return (d.get('Hydro', -1), d.get('Water', -1), d.get('Heat', -1))

def process_item_list(LID: int, apps: list) -> tuple:
    '''
    USED TO PROCESS
    -Amenities,
    -Appliances
    -Personal Outdoor Space
    All are in  h4 tags, and can be a variety
    of items stored in a ul or 'Not Included'
    the parsing function drops them into a list
    so this function pairs them with the LID
    in a tuple for easier insertion to the db
    '''
    return [(LID, app) for app in apps]

def process_numeric(n: str, default) -> int:
    '''
    takes numerical value stored as a str
    like price or sqft and the default value inserted
    when it is not provided
    and returns the numical value as an integer
    Typically price is formatted $X,XXX or 'Please Contact'
    Sqft is either a number or 'Not Available'
    So try to extract the number formatting and return
    an integer.
    Price is in the data stripped out of the title
    '''
    if p == default:
        return -1
    try:
        return int(p.translate(str.maketrans('', '', '$,')))
    except:
        return -1

def process_bb(bb_str: str) -> float:
    '''
    process bedroom and bathroom str
    bathrooms will be an int (1-4+) or a float with a .5
    bedrooms with be a range 1 to n and could include a Den
    or be a 'Bachelor/Studio'
    str will be in format Facility: N
    i.e. Bedrooms 1 + Den or Bathrooms: 1.5
    and is present in the u data structure
    '''
    fac, val = bb_str.split(':')
    if fac == 'Bedrooms':
        if 'Bachelor/Studio' in val:
            return 0
        if ' + Den' in val:
            v = val.split('+')
            return float(v[0].strip()) + 0.5)
    return float(val.strip())

