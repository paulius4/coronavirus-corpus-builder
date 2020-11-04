import os

import pandas as pd
from dateutil.parser import parse

from corpus_builder.tweet_hydration.settings import TEMP_DIR

# Process the following dataset: https://zenodo.org/record/3871753
TWEET_IDS_DIR = os.path.join(TEMP_DIR, 'tweet-ids-TweetsCOV19/')
TSV_PATH = os.path.join(TWEET_IDS_DIR, 'TweetsCOV19.tsv')
START_DATE = parse('2019-12-01').date()
END_DATE = parse('2020-03-19').date()

HEADER_LIST = ['id', 'username', 'timestamp', 'followers', 'friends', 'retweets', 'favorites', 'entities', 'sentiment',
               'mentions', 'hashtags', 'urls']

FILENAME_TEMPLATE = "{date}_tweets_cov19.csv"

CHUNK_SIZE = 200000

if __name__ == '__main__':
    for df_chunk in pd.read_csv(TSV_PATH, sep='\t', names=HEADER_LIST, chunksize=CHUNK_SIZE):
        dates_result = [parse(timestamp).date() for timestamp in df_chunk['timestamp']]
        df_chunk['date'] = dates_result

        groupby_results = df_chunk.groupby('date')

        for date, df in groupby_results:
            date_str = date.strftime('%Y-%m-%d')
            filename = FILENAME_TEMPLATE.format(date=date)
            filepath = os.path.join(TWEET_IDS_DIR, filename)
            count_rows = df.shape[0]
            print(f'Appending {count_rows} records to {filepath}')
            df.to_csv(filepath, mode='a', index=False, header=not os.path.exists(filepath))
