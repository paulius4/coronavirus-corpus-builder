import argparse
import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))
from corpus_builder.reddit_processing.reddit_processing import process_reddit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='process_reddit.py',
                                     description='Output the Reddit dataset in a standard format')
    parser.version = '1.0'
    parser.add_argument('input_dir', action='store',
                        help=f'Directory where the source Reddit dataset is stored (see README.md)')

    parser.add_argument('-o', '--output_dir', action='store',
                        help='Directory where to save the posts (default: current working directory)')
    parser.add_argument('-l', '--limit', action='store', type=int,
                        help='How many posts to export at most (default: all available)')

    parser.set_defaults(limit=None, output_dir=os.getcwd())
    args = parser.parse_args()

    process_reddit(args.input_dir, args.output_dir, args.limit)

