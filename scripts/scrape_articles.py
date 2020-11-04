import argparse
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))
from corpus_builder.scraping.gov_uk_news import scrape_gov_uk_news
from corpus_builder.scraping.guardian import scrape_guardian
from corpus_builder.scraping.sun import scrape_sun
from corpus_builder.scraping.telegraph import scrape_telegraph
from corpus_builder.scraping.weforum import scrape_weforum

from config import DEFAULT_WAIT_TIME
from corpus_builder.database.database import Source

VALID_SOURCES = [Source.GOV_UK_NEWS, Source.TELEGRAPH, Source.GUARDIAN, Source.SUN, Source.WEFORUM]



if __name__ == '__main__':
    sources_listing = ', '.join([s.name.lower() for s in VALID_SOURCES])

    parser = argparse.ArgumentParser(prog='scrape_articles.py',
                                     description='Scrape coronavirus-related articles')
    parser.version = '1.0'
    parser.add_argument('source', action='store',
                        help=f'A source to scrape articles from. Valid options: {sources_listing}')

    parser.add_argument('-l', '--limit', action='store', type=int,
                        help='How many articles to scrape at most (default: all available)')
    parser.add_argument('-w', '--wait', action='store', type=int,
                        help=f'Wait time between requests (default: {DEFAULT_WAIT_TIME})')
    parser.set_defaults(limit=None, wait=DEFAULT_WAIT_TIME)

    args = parser.parse_args()

    try:
        chosen_source = Source[args.source.upper()]
        assert chosen_source in VALID_SOURCES
    except (KeyError, AssertionError):
        parser.error(f'{args.source} is not a valid source.\n\tValid sources: {sources_listing}')
        sys.exit()

    if chosen_source == Source.GOV_UK_NEWS:
        scrape_gov_uk_news(args.limit, args.wait)
    elif chosen_source == Source.TELEGRAPH:
        scrape_telegraph(args.limit, args.wait)
    elif chosen_source == Source.GUARDIAN:
        scrape_guardian(args.limit, args.wait)
    elif chosen_source == Source.SUN:
        scrape_sun(args.limit, args.wait)
    elif chosen_source == Source.WEFORUM:
        scrape_weforum(args.limit, args.wait)
