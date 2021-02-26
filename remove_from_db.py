from tinydb import TinyDB, where
from glob import glob
import os, sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser('Remove folder from sent db.')
    parser.add_argument('dirname_regex', type=str)
    args = parser.parse_args()

    filenames = glob('./data/{}/*'.format(args.dirname_regex))

    if len(filenames) == 0:
        print('Nothing matched!')
        sys.exit(0)

    for fn in filenames:
        print(fn)
    confirm = input('Confirm [y/N]:')

    if confirm.lower().strip() == 'y':
        print('Confirmed!')
        db = TinyDB('./data/db.json')
        for fn in [os.path.basename(fn) for fn in filenames if 'article' not in fn]:
            db.remove(where('filename') == fn)
            print('{} removed!'.format(fn))
    else:
        print('Nothing happened!')
