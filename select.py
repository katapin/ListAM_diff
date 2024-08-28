"""Query information from the state file."""

import sys
import argparse
from operator import attrgetter

from common import *


def select(infile: str, sortkey: str, desc_ord: bool = False,
           lprice: int = None, uprice: int = None):
    rawdata = read_json(infile)['data']  # list for dicts
    data = [Card(**c) for c in rawdata]  # list of cards
    if lprice or uprice:
        data = filter(
            lambda x, l = lprice or 0.0, u = uprice or float('inf'):
                l <= x.price <= u,
            data
        )
    return sorted(data, key=attrgetter(sortkey), reverse=desc_ord)


def select_and_save(infile: str, reportfile: str, **selectargs):
    g = Gallery(select(infile, **selectargs),
                title=f'Select from {infile} with {selectargs}')
    save_html(reportfile, galleries=[g], pagetitle=infile)
    print(f'Saved {reportfile}')



def _main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('infile', nargs=1,
                           help="Files to compare")
    argparser.add_argument('reportfile', nargs=1,
                           help="Filename to same an html report")
    argparser.add_argument('--sort', nargs='?',
                           choices=['id', 'price'], default='price',
                           help="Sort by")
    argparser.add_argument('--order', nargs='?',
                           choices=['asc', 'desc'], default='asc',
                           help="Sorting order, ascending or descending")
    argparser.add_argument('--lprice', nargs='?',
                           help="Lower price limit", type=int)
    argparser.add_argument('--uprice', nargs='?',
                           help="Upper price limit", type=int)
    argnspace = argparser.parse_args(sys.argv[1:])

    select_and_save(
        argnspace.infile[0], argnspace.reportfile[0], sortkey=argnspace.sort,
        lprice=argnspace.lprice, uprice=argnspace.uprice,
        desc_ord=True if argnspace.order == 'desc' else False
    )

if __name__ == '__main__':
    _main()