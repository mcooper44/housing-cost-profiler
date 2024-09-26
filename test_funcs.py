from kijiji import get_page
from kijiji import parse_result
from kijiji import get_l_details_dl
from kijiji import get_l_details_h4
from kijiji import get_l_title_details
from kijiji import get_l_unit_type
from kijiji import get_l_key
from kijiji import get_l_features
from kijiji import create_a_listing
from kijiji import a_listing
from kijiji import MAIN_STR3, TARGETS
from kijiji import generate_url_list




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

def test_a_listing(target: str):
        key = get_l_key(target) # grab unique listing key
        page = get_page(target) # get html
        data = parse_result(page) # parse with bs4
        # extract features
        f, f2 = get_l_features(data)
        return create_a_listing(key, f, f2, target)


def test_link_process(links):
    data_links = {}
    for link in links:
        print(link)
        print('...')
        f = None
        f2 = None
        l = None
        # get key, html and parse it
        #target = f'{base}{link}'
        target = link
        print(target)
        key = get_l_key(target) # grab unique listing key
        try:
            print('getting page')
            page = get_page(target) # get html
            data = parse_result(page) # parse with bs4
            print('got data... sleeping')
            sleep(4) # courtesy pause
            # extract features
            if data:
                data_links[key] = [data]
                print('saved data')
            else:
                print(f'{key} : no data')
            try:
                f, f2 = get_l_features(data)
                l = create_a_listing(key, f, f2, target)
            except Exception as e:
                print('process_links: could not extract features or create a_listing')
                print(f'key: {key}, target: {target} f:{f} f2:{f2}')

            if l:
                out = l.get_base_str() + [TDATE]
                print('csv output:')
                print(out)
            else:
                print('failed to create csv summary')
        except:
            print(f'key {key} failed. Could not get page or parse result')
    return data_links


def test_main():
    roots = [(MAIN_STR3,TARGETS[2])]
    link_listing = [] # pinged links
    data_listings = [] 

    for root, parts in roots:
        url_list = generate_url_list(START, PAGES, root, parts)
        print(url_list)
        for url in url_list:
            print(url)
            page = get_page(url)
            print('got page')
            sleep(1)
            if page:
                data = parse_result(page)
                link_list = get_links(data)
                link_listing.append(link_list)
                try:
                    tl = test_link_process(link_list)
                    data_listings.append(tl)
                except:
                    print('could not test link_process')
            else:
                print('could not get page')
    return {'links': link_listing,
            'data_listings': data_listings}
