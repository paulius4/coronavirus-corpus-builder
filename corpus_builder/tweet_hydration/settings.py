from os.path import join
from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parent.parent.parent
TEMP_DIR = join(PROJECT_ROOT_DIR, 'temp/')
OUTPUT_DIR = join(PROJECT_ROOT_DIR, 'output/')

TWEETS_HYDRATED_DIR = join(OUTPUT_DIR, 'tweets-hydrated/')
TWEET_IDS_DIR_DATAPORT = join(TEMP_DIR, 'tweet-ids-dataport')
TWEET_IDS_DIR_TWEETS_COV19 = join(TEMP_DIR, 'tweet-ids-TweetsCOV19')
HYDRATION_PROGRESS = join(TEMP_DIR, 'tweet-hydration-progress.json')
SKIPPED_IDS_RETWEETS = join(TWEETS_HYDRATED_DIR, 'tweet-ids-skipped-retweets.txt')
