"""Compare to state files."""
import sys
import argparse
from datetime import datetime
from common import *


def compare(file1: str, file2: str, *, reportfile: str = None):
    json1, json2 = read_json(file1), read_json(file2)
    if json1['meta']['parameters'] != json2['meta']['parameters']:
        print("Error: Can't compare file produced with query parameters.")
        exit(1)
    date1 = datetime.fromisoformat(json1['meta']['date_created']['start_date'])
    date2 = datetime.fromisoformat(json2['meta']['date_created']['start_date'])
    if date1 < date2:
        ofile, odate, odatalst = file1, date1, json1['data']
        nfile, ndate, ndatalst = file2, date2, json2['data']
    else:
        ofile, odate, odatalst = file2, date2, json2['data']
        nfile, ndate, ndatalst = file1, date1, json1['data']

    ostrdate = odate.isoformat()
    nstrdate = ndate.isoformat()
    lw = max(len(ofile), len(ostrdate))
    rw = max(len(nfile), len(nstrdate))
    uw = max([len(c['fullurl']) for c in odatalst])
    print('+'*(uw+11+rw)) # +++++
    print(f"{'':{uw+7-lw}}{'OLD':^{lw}} -> {'NEW':^{rw}}")
    print(f"{'':{uw+7-lw}}{ofile:^{lw}} -> {nfile:^{rw}}")
    print(f"{'':{uw+7-lw}}{ostrdate:^{lw}} -> {nstrdate:^{rw}}")
    print('+'*(uw+11+rw)) # +++++

    odct = {c['id']: Card(**c) for c in odatalst}   # cards from older file
    ndct = {c['id']: Card(**c) for c in ndatalst}   # cards from fresher file
    sold, snew = set(odct), set(ndct)
    salt, spr = set(), set()     # different

    # Get gone, new and changed
    for id in odct:  # We are going to modify original dict
        if id in ndct:
            if odct[id] != ndct[id]:
                salt.add(id)   # Add to changed
            sold.remove(id)    # Remain only deleted
            snew.remove(id)    # Remain only new

    # Investigate what was changed.
    for id in tuple(salt):
        if odct[id].price != ndct[id].price:
            spr.add(id)
            salt.remove(id)

    print(f'Changed price:  {len(spr)}')
    for id in sorted(spr):
        print(f"{ndct[id].fullurl:{uw}} {odct[id].price:{6}} -> {ndct[id].price:{6}}")

    print(f'Other changes:  {len(salt)}')
    for id in sorted(salt):
        print(f"{ndct[id].fullurl:{uw}} {ndct[id].price:^{6}}")

    print(f'New:   {len(snew)}')
    for id in sorted(snew):
        print(f"{ndct[id].fullurl:{uw}} {ndct[id].price:^{6}}")

    print(f'Gone:  {len(sold)}')
    for id in sorted(sold):
        print(f"{odct[id].fullurl:{uw}}")

    if reportfile:
        gnew = Gallery([ndct[id] for id in sorted(snew)], title='New')
        gpr = Gallery([ndct[id] for id in sorted(spr)], title='Changed  their price')
        galt = Gallery([ndct[id] for id in sorted(spr)], title='Other changes')
        save_html(reportfile, galleries=[gnew, gpr, galt],
                  pagetitle=f"{ofile} vs {nfile}")



def _main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('file', nargs=2,
                               help="Files to compare")
    argparser.add_argument('--html', nargs='?',
                           help="Create html report")

    argnspace = argparser.parse_args(sys.argv[1:])

    compare(*argnspace.file, reportfile=argnspace.html)


if __name__ == '__main__':
    _main()