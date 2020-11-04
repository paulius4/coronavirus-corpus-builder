import argparse
import pathlib
import sys
import os

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))
from corpus_builder.export.export import export_articles, export_sample_docx
from corpus_builder.database.database import Source

VALID_SOURCES = [Source.GOV_UK_NEWS, Source.TELEGRAPH, Source.GUARDIAN, Source.SUN, Source.WEFORUM]

if __name__ == '__main__':
    sources_listing = ', '.join([s.name.lower() for s in VALID_SOURCES])

    parser = argparse.ArgumentParser(prog='export_articles.py',
                                     description='Export articles collected by scrape_articles.py')
    parser.version = '1.0'
    parser.add_argument('source', action='store',
                        help=f'Export articles collected from this source. Valid options: {sources_listing}')

    parser.add_argument('-l', '--limit', action='store', type=int,
                        help='How many articles to export most (default: all available)')
    parser.add_argument('-o', '--output_dir', action='store',
                        help='Directory where to save the articles (default: current working directory)')
    parser.add_argument('-d', '--docx', action='store_true',
                        help='Export a sample of articles in .docx format (default: no). Default limit for .docx: 200')

    parser.set_defaults(limit=None, output_dir=os.getcwd(), docx=False)

    args = parser.parse_args()

    try:
        chosen_source = Source[args.source.upper()]
        assert chosen_source in VALID_SOURCES
    except (KeyError, AssertionError):
        parser.error(f'{args.source} is not a valid source.\n\tValid sources: {sources_listing}')
        sys.exit()

    if not args.docx:
        export_articles(chosen_source, args.output_dir, args.limit)
    else:
        if args.limit:
            export_sample_docx(chosen_source, args.output_dir, args.limit)
        else:
            export_sample_docx(chosen_source, args.output_dir)