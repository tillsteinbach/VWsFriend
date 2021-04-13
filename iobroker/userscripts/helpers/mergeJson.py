#!/usr/bin/python3
 
import json
import argparse
import sys
from pprint import pprint

def merge(a, b, path=None, overwrite=False):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)], overwrite)
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                if overwrite:
                    a[key] = b[key]
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

parser = argparse.ArgumentParser(
    description='Change json settings')
parser.add_argument('--infile', '-i', nargs='?', type=argparse.FileType('r', encoding='UTF-8'), default=sys.stdin)
parser.add_argument('--outfile', '-o', nargs='?', type=argparse.FileType('w', encoding='UTF-8'), default=sys.stdout)
parser.add_argument('mergefile', nargs='+', type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--overwrite', action='store_true')


args = parser.parse_args()

inputDict = json.load(args.infile)

for mergefile in args.mergefile:
    mergedict = json.load(mergefile)
    merged = merge(inputDict, mergedict, overwrite=args.overwrite)

json.dump(inputDict, args.outfile)
