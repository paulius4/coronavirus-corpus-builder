import argparse
import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))
from corpus_builder.cord19_processing.cord19_processing import process_cord19, generate_cord19_docx_sample

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='process_cord19.py',
                                     description='Output the CORD-19 dataset in a standard format')
    parser.version = '1.0'
    parser.add_argument('input_dir', action='store',
                        help=f'Directory where the source CORD-19 dataset is stored (see README.md)')

    parser.add_argument('-o', '--output_dir', action='store',
                        help='Directory where to save the articles (default: current working directory)')

    parser.add_argument('-l', '--limit', action='store', type=int,
                        help='How many articles to export at most (default: all available)')
    parser.add_argument('-d', '--docx', action='store_true',
                        help='Export a sample of articles in .docx format (default: no). Default limit for .docx: 200')

    parser.set_defaults(limit=None, output_dir=os.getcwd())

    args = parser.parse_args()

    if not args.docx:
        process_cord19(args.input_dir, args.output_dir, args.limit)
    else:
        if args.limit:
            generate_cord19_docx_sample(args.input_dir, args.output_dir, args.limit)
        else:
            generate_cord19_docx_sample(args.input_dir, args.output_dir)