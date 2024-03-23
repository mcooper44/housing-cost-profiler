from ez_address_parser import AddressParser


def process_ap(lst, lbl, max_rep=2):
    r = []
    for t in lst:
        v,l = t
        if l == lbl:
            if len(r) < max_rep:
                r.append(v)
    return ' '.join(r) if r else None

def get_sa(lst):
    ls = ['StreetNumber', 'StreetName', 'StreetType',
          'StreetDirection']
    s = []
    for v in ls:
        t = process_ap(lst, v)
        if t:
            s.append(t)
    return ' '.join(s) if s else None


def process_address(address):
    ap = AddressParser()
    t = ap.parse(address)
    city = process_ap(t, 'Municipality', 1)
    pcode = process_ap(t, 'PostalCode')
    street = get_sa(t)
    return (street, city, pcode)
