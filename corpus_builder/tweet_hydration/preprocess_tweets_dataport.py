import os
from os import listdir
from os.path import isfile, join

import dateutil
import pandas as pd
from dateutil.parser import parse
from twarc import Twarc

# Process the following dataset: https://ieee-dataport.org/open-access/coronavirus-covid-19-tweets-dataset
from corpus_builder.tweet_hydration.settings import TEMP_DIR

HEADER_LIST = ['id', "sentiment_score"]
TWEET_IDS_DIR = os.path.join(TEMP_DIR, 'tweet-ids-dataport/')
twarc_instance = Twarc()

csv_files = [join(TWEET_IDS_DIR, f) for f in listdir(TWEET_IDS_DIR) if isfile(join(TWEET_IDS_DIR, f))]

for filepath in csv_files:
    df = pd.read_csv(filepath, names=HEADER_LIST, nrows=100)
    ids_to_hydrate = list(df.iloc[:, 0])
    hydrated_tweet = ''
    for id in ids_to_hydrate:
        try:
            hydrated_tweet = next(twarc_instance.hydrate([id]))
            break
        except StopIteration:
            print(f'Failed to hydrate {id}')
            pass

    date = dateutil.parser.parse(hydrated_tweet['created_at']).date()
    date_str = date.strftime('%Y-%m-%d')

    filename = os.path.basename(filepath)
    new_filepath = filepath.replace('corona_tweets_', f'{date_str}_corona_tweets_')

    print(filepath, date_str)
    print(new_filepath)
    print('*****')

    os.rename(filepath, new_filepath)
