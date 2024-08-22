import sys
import time
import random
import argparse
from datetime import datetime

from urllib import request as ureq
from bs4 import BeautifulSoup, Tag

from common import *


class MyHTTPRedirectHandler(ureq.HTTPRedirectHandler):
    """Remember that the destination was redirected."""
    def http_error_302(self, req, fp, code, msg, headers):
        resp = super().http_error_302(req, fp, code, msg, headers)
        resp.is_redirected = True
        return resp


ureq.install_opener(ureq.build_opener(MyHTTPRedirectHandler))  # Install handler


#### Functions


def sleep_random(b: int = 30, a: int = 1):
    """Sleep random time."""
    time.sleep(random.randint(a, b))


def construct_category_url(category: int, location: str, page: int = 1,
                           sid: int = None, lprice: int = None, uprice: int = None,
                           curency: int = 0) -> str:
    params = [f'n={location}', f'crc={curency}']  # crc=0 is AMD, crc=2 is 'not selected'
    if lprice:
        params.append(f'price1={lprice}')
    if uprice:
        params.append(f'price2={uprice}')
    if sid:
        params.append(f'sid={sid}')
    url = base_url + f'/category/{category}'
    if page > 1:
        url+= f'/{page}'
    return url + '?' + '&'.join(params)


def request_url(url: str, extra_headers: dict = None, method: str = 'GET'):
    if extra_headers:
        headers = base_headers.copy()
        headers.update(extra_headers)
    else:
        headers = base_headers

    request = ureq.Request(url, headers=headers, method=method)
    resp = ureq.urlopen(request)
    if resp.status != 200:
        raise ValueError("Something is going wrong. The server answered "
                         f"{resp.status} for '{url}.")

    if resp.headers['Set-Cookie']:  # Save cookie
        base_headers['Cookie'] = resp.headers['Set-Cookie'] + '; lang=0'
    return resp


def parse_showcase(soup: BeautifulSoup) -> list:
    """Parse a single page with many cards."""
    gls = soup.findAll('div', attrs={'class': 'gl'})  # aggregator tag of cards <div class="gl>
    gl = gls[-1]  # gls[0] - VIP cards, gls[1] - regular
    result = []
    for a in gl:  # <a href> tag
        card = Card.from_tag(a)
        result.append(card)
    return result


def go_through_showcases(request_parameters: dict) -> dict:
    """Browse all available pages."""
    res = {}
    for curpage in range(1,21):  # Don't lookup higher pages
        url = construct_category_url(page=curpage, **request_parameters)
        print(f'Requesting {url}...')
        responce = request_url(url)
        if getattr(responce, 'is_redirected', False) is True:
            print("  Doesn't exist. Exiting...")
            break

        foundcards = parse_showcase(BeautifulSoup(
            responce.read(), "lxml"))
        print(f"  Found {len(foundcards)}")
        res[curpage] = foundcards
        sleep_random(sleeptime)
    return res


def process_and_save(outfileroot: str, request_parameters: dict,
                     origin: str = None):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    outfile='{}_{}.json'.format(
        outfileroot,
        f'{timestamp}' if origin else f'origin-{timestamp}'
    )

    startdate = datetime.now().isoformat()
    carddict = go_through_showcases(request_parameters)
    enddate = datetime.now().isoformat()
    cardlist = [card for lst in carddict.values() for card in lst]
    data = {
        'meta': {
            'date_created': {
                'start_date': startdate,
                'end_date': enddate
            },
            'date_filled': {
                'start_date': None,
                'end_date': None
            },
            'parameters': request_parameters,
            'pages': len(carddict),
            'cards': len(cardlist),
            'origin':origin
        },
        'data': cardlist
    }
    write_json(outfile, data)
    print(f"Saved '{outfile}'.")


def command_create(fileroot: str, category_str: str, location: str,
               lprice: int = None, uprice: int = None, sid: int = None):
    """Process the 'create' command."""
    _l = category_str.split('-')
    category = int(_l[0])
    sid = int(_l[1]) if len(_l) > 1 else None
    request_parameters = dict(
        category=category,       # Category from the left panel
        sid=sid,                 # 'Type' within the chosen category (from the dropdown)
        location=location,
        lprice=lprice,
        uprice=uprice
    )
    process_and_save(fileroot, request_parameters)


def command_update(infile: str):
    """Process 'update' command."""
    data = read_json(infile)
    meta = data['meta']
    origin = data['meta']['origin'] or infile
    outfileroot = '_'.join(origin.split('_')[:-1])
    process_and_save(outfileroot, meta['parameters'], origin)


def _main():
    mainargparser = argparse.ArgumentParser()
    subparsers = mainargparser.add_subparsers(dest='command')
    parser_create = subparsers.add_parser('create')
    parser_create.add_argument('nameroot', nargs=1,
                               help="Root filename")
    parser_create.add_argument('--category', nargs='?',
                               help="Category and subcategory (type) numbers separated "
                               "with a hyphen, e.g. '99-200'", required=True)
    parser_create.add_argument('--location', nargs='?',
                               help="location codes, default is '1' for Yerevan",
                               default='1')
    parser_create.add_argument('--lprice', nargs='?', help="Lower price limit")
    parser_create.add_argument('--uprice', nargs='?', help="Upper price limit")
    parser_update = subparsers.add_parser('update')
    parser_update.add_argument('reffile', nargs=1, help="Reference file")
    parser_update = subparsers.add_parser('fill')
    parser_update.add_argument('filename', nargs=1, help="File to fill unfilled fields.")

    argnspace = mainargparser.parse_args(sys.argv[1:])
    if argnspace.command == 'create':
        command_create(argnspace.nameroot[0], category_str=argnspace.category,
                   location=argnspace.location, lprice=argnspace.lprice,
                   uprice=argnspace.uprice)
    elif argnspace.command == 'update':
        command_update(argnspace.reffile[0])
    elif argnspace.command == 'fill':
        pass


if __name__ == '__main__':
    _main()
