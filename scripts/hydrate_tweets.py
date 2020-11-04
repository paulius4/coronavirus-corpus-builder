import argparse
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))
from corpus_builder.tweet_hydration.tweet_hydration import hydrate_tweets

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='hydrate_tweets.py',
                                     description='Download information about tweet IDs provided '
                                                 '(settings found in corpus_builder/tweet_hydration/settings)')
    parser.version = '1.0'
    args = parser.parse_args()
    hydrate_tweets()
