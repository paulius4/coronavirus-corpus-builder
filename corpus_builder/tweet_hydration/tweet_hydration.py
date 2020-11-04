import json
import math
import os
import string
from os import listdir
from os.path import join, isfile
from pathlib import Path
from pprint import pprint

import dateutil.parser
import geograpy
import pandas as pd
import pycountry
import us
from tqdm import tqdm
from twarc import Twarc

from config import JSON_INDENT
from corpus_builder.tweet_hydration.settings import TWEET_IDS_DIR_DATAPORT, \
    TWEET_IDS_DIR_TWEETS_COV19, TWEETS_HYDRATED_DIR, HYDRATION_PROGRESS, SKIPPED_IDS_RETWEETS
from corpus_builder.utilities import replace_linebreaks

SELECTED_COLUMNS = ['id']
COLUMN_NAMES_DATAPORT = ['id', 'sentiment_score']
BATCH_SIZE = 45000
twarc_instance = Twarc()


def get_tweet_ids_csv_filepaths():
    dataport_ids = [join(TWEET_IDS_DIR_DATAPORT, f) for f in listdir(TWEET_IDS_DIR_DATAPORT) if
                    isfile(join(TWEET_IDS_DIR_DATAPORT, f))]

    cov19_ids = [join(TWEET_IDS_DIR_TWEETS_COV19, f) for f in listdir(TWEET_IDS_DIR_TWEETS_COV19) if
                 isfile(join(TWEET_IDS_DIR_TWEETS_COV19, f))]

    return sorted(dataport_ids + cov19_ids)


def get_tweets_hydrated_filename(ids_filename, batch_num, json):
    if json:
        ext = 'json'
    else:
        ext = 'txt'

    filename = f'{ids_filename[:11]}_{batch_num:02}.{ext}'
    return join(TWEETS_HYDRATED_DIR, filename)


def get_tweet_lengths_filename(ids_filename, batch_num):
    filename = f'{ids_filename[:11]}_{batch_num:02}.csv'
    return join(TWEETS_HYDRATED_DIR, 'lengths/', filename)


def get_overall_progress():
    try:
        with open(HYDRATION_PROGRESS, 'rb') as f:
            progress = json.load(f)
    except IOError:
        print('Progress file not found. Creating a new progress file...')
        progress = {}
        filepaths = get_tweet_ids_csv_filepaths()

        for i in tqdm(range(0, len(filepaths)), desc='Computing required batch count for each CSV'):
            df = pd.read_csv(filepaths[i])
            total_iterations_needed = int(math.ceil(len(df.index) / BATCH_SIZE))
            progress[os.path.basename(filepaths[i])] = {'last_batch': -1, 'total_batches': total_iterations_needed}

        progress['last_started_batch_index'] = 0
        progress['last_processed_file_index'] = -1
        progress['batches_log'] = []

        Path(HYDRATION_PROGRESS).parent.mkdir(parents=True, exist_ok=True)
        with open(HYDRATION_PROGRESS, 'wb') as f:
            json.dump(progress, f, sort_keys=True, indent=4)

    pprint(progress)
    return progress


def extract_tweet_location(tweet):
    usa_states_abbreviations = [state.abbr for state in us.states.STATES]
    location = None
    if tweet['place']:
        location = tweet['place']['country']
    elif tweet['user']['location']:
        user_location_words = tweet['user']['location'].split()
        table = str.maketrans('', '', string.punctuation)
        user_location_words = [w.translate(table) for w in user_location_words]

        # Full country name
        for country in pycountry.countries:
            if country.name in tweet['user']['location']:
                location = country.name

        # US state abbreviations (very common)
        if not location:
            for word in user_location_words:
                if word in usa_states_abbreviations:
                    location = 'United States'

        # Country abbreviations
        if not location:
            for country in pycountry.countries:
                # 2-letter abbreviations
                if country.alpha_2 in user_location_words:
                    location = country.name
                    break
                # The pycountry library uses 'GBR' and doesn't include 'UK', which is used more commonly
                if 'UK' in user_location_words:
                    location = 'United Kingdom'
                    break
                # 3-letter abbreviations
                if country.alpha_3 in user_location_words:
                    location = country.name
                    break

        if not location:
            places = geograpy.get_place_context(text=tweet['user']['location'])
            if places.countries:
                location = places.countries[0]

    return location


def hydrate_tweet_slice(ids_to_hydrate):
    hydrated_tweets = []
    for i in tqdm(range(0, len(ids_to_hydrate), 100), desc='Hydrating tweets'):
        hydrated = twarc_instance.hydrate(ids_to_hydrate[i:i + 100])
        hydrated_tweets.extend(hydrated)
    return hydrated_tweets


def process_tweet(tweet):
    content = replace_linebreaks(tweet['full_text'])
    date = dateutil.parser.parse(tweet['created_at']).date()
    hashtags = [hashtag['text'] for hashtag in tweet['entities']['hashtags']]
    urls = [url['expanded_url'] for url in tweet['entities']['urls']]
    user_mentions = [mention['id'] for mention in tweet['entities']['user_mentions']]
    location = extract_tweet_location(tweet)

    processed_metadata = {}
    processed_metadata['date'] = date.strftime('%Y-%m-%d')
    processed_metadata['location'] = location
    processed_metadata['hashtags'] = hashtags
    processed_metadata['urls'] = urls
    processed_metadata['user_mentions'] = user_mentions
    processed_metadata['id'] = tweet['id']
    processed_metadata['language'] = tweet['lang']
    processed_metadata['favourite_count'] = tweet['favorite_count']
    processed_metadata['retweet_count'] = tweet['retweet_count']
    processed_metadata['in_reply_to_status_id'] = tweet['in_reply_to_status_id']
    processed_metadata['in_reply_to_user_id'] = tweet['in_reply_to_user_id']
    processed_metadata['author'] = tweet['user']['id']
    processed_metadata['author_name'] = tweet['user']['name']
    processed_metadata['author_followers_count'] = tweet['user']['followers_count']
    processed_metadata['author_statuses_count'] = tweet['user']['statuses_count']
    processed_metadata['author_verified'] = tweet['user']['verified']
    return content, processed_metadata


def hydrate_tweets():
    batch_start = 0
    batch_end = 10
    progress = get_overall_progress()

    filepaths = get_tweet_ids_csv_filepaths()
    for batch_index in range(batch_start, batch_end):
        for filepath_index in range(progress['last_processed_file_index'] + 1, len(filepaths)):
            filepath = filepaths[filepath_index]
            base_filename = os.path.basename(filepath)
            total_batches = progress[base_filename]['total_batches']

            print(f'Processing file {base_filename}. Current batch index: {batch_index}, '
                  f'total batches for file: {total_batches}')

            if batch_index > total_batches - 1:
                print(f'Skipping {filepath} (already fully processed)')
                continue
            if progress[base_filename]['last_batch'] >= batch_index:
                print(f'Skipping {filepath} (current batch already processed)')
                continue

            try:
                # TweetsCOV19
                df = pd.read_csv(filepath, usecols=SELECTED_COLUMNS)
            except ValueError:
                # Dataport
                df = pd.read_csv(filepath, names=COLUMN_NAMES_DATAPORT, usecols=SELECTED_COLUMNS)

            start_index = BATCH_SIZE * batch_index
            end_index = (BATCH_SIZE * batch_index) + BATCH_SIZE

            print(f'Start index: {start_index}, end index: {end_index}')
            ids_to_hydrate = list(df.iloc[start_index:end_index, 0])

            output_txt_path = get_tweets_hydrated_filename(base_filename, batch_index, json=False)
            output_json_path = get_tweets_hydrated_filename(base_filename, batch_index, json=True)
            output_lengths_csv_path = get_tweet_lengths_filename(base_filename, batch_index)
            Path(output_txt_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_lengths_csv_path).parent.mkdir(parents=True, exist_ok=True)

            print(f'len(df) {len(df)}')
            print(f'len(ids_to_hydrate) {len(ids_to_hydrate)}')
            hydrated_tweets = hydrate_tweet_slice(ids_to_hydrate)
            print(f'Hydrating tweets completed...')
            print(f'len(hydrated_tweets) = {len(hydrated_tweets)}')

            filtered_content = []
            filtered_tweets = []
            tweet_length_info_list = []
            skipped_tweet_ids_retweets = []

            for i in tqdm(range(0, len(hydrated_tweets)), desc='Processing hydrated tweets'):
                tweet = hydrated_tweets[i]
                try:
                    # Exception thrown if tweet is a retweet
                    _ = tweet['retweeted_status']
                    skipped_tweet_ids_retweets.append(tweet['id_str'])
                    # Skip if this is a retweet
                    continue
                except KeyError:
                    content = tweet['full_text']
                    tweet_length = len(content.split())
                    tweet_length_info = {'tweet_id': tweet['id_str'],
                                         'tweet_length': tweet_length}
                    tweet_length_info_list.append(tweet_length_info)

                    content, processed_metadata = process_tweet(tweet)
                    filtered_tweets.append(processed_metadata)
                    filtered_content.append(content)

            df_tweet_lengths = pd.DataFrame(tweet_length_info_list)
            df_tweet_lengths.to_csv(output_lengths_csv_path, encoding='utf-8', index=False)

            with open(output_json_path, 'w') as outfile_json:
                json.dump(filtered_tweets, outfile_json, sort_keys=True, indent=JSON_INDENT)

            with open(output_txt_path, 'w') as outfile_txt:
                for tweet, content in tqdm(zip(filtered_tweets, filtered_content), desc='Writing tweets to disk'):
                    outfile_txt.write(f'{tweet["id"]}\t{content}\n')

            with open(SKIPPED_IDS_RETWEETS, 'a') as fh:
                fh.write('\n'.join(skipped_tweet_ids_retweets))

            progress['last_started_batch_index'] = batch_index

            if filepath_index == len(filepaths) - 1:
                progress['last_processed_file_index'] = -1
            else:
                progress['last_processed_file_index'] = filepath_index

            progress[base_filename]['last_batch'] = batch_index
            batches_long_entry = {'batch_index': batch_index,
                                  'base_filename': base_filename,
                                  'num_tweets_saved': len(filtered_tweets)}
            progress['batches_log'].append(batches_long_entry)

            with open(HYDRATION_PROGRESS, 'wb') as f:
                json.dump(progress, f, sort_keys=True, indent=4)

            print(f'Batch {batch_index} for {base_filename} completed!')
            print('*' * 80)
