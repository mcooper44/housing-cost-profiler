from ez_address_parser import AddressParser
from typing import Union

def process_ap(lst: list, lbl: str, max_rep: int=2):
    '''
    take an ez-address-parser list and a specific
    label and return a string made of up thos elements
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
    into labelled element, label pairs

    call the helper functions process_ap and get_sa to separate
    out the elements needed for the database

    return a tuple of (street string, city string, postal code string)
    '''
    ap = AddressParser()
    t = ap.parse(address)
    city = process_ap(t, 'Municipality', 1)
    pcode = process_ap(t, 'PostalCode')
    street = get_sa(t)
    return (street, city, pcode)


def process_utility(utility: list) -> dict:
