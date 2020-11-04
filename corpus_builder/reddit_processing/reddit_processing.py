import datetime
import os
from pathlib import Path

import pandas as pd

from config import JSON_INDENT


def get_last_day_of_week(week_from_publication):
    publication_start_week = 5
    calendar_week = publication_start_week + week_from_publication - 1

    monday = datetime.datetime.strptime(f'2020-{calendar_week}-1', "%Y-%W-%w").date()
    sunday = monday + datetime.timedelta(days=6.99)
    return sunday.strftime("%Y-%m-%d")


def is_valid_post(x):
    invalid_post_strings = [
        'Thank you for your submission! Unfortunately, your submission has been removed',
        'Thanks for your submission, but it has been removed for the following reason',
        'Thanks for contributing! Unfortunately your submission has been removed',
        'Unfortunately, your post has been removed for the following reason(s)',
        'post has been removed. Attempts to circumvent this filter will result in a ban.',
        'but it has been removed because it doesn\'t quite abide by our rules, which are located in the sidebar.',
        '(#start_removal)']

    for string in invalid_post_strings:
        if string in x['post']:
            return False

    return True


def process_reddit(input_dir, output_dir, limit=None):
    if not os.path.isabs(input_dir):
        input_dir = os.path.join(os.getcwd(), input_dir)
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.getcwd(), output_dir)

    data_f_csv = os.path.join(input_dir, 'data.F.v.csv')
    data_m_csv = os.path.join(input_dir, 'data.M.v.csv')
    df_female = pd.read_csv(data_f_csv)
    df_male = pd.read_csv(data_m_csv)

    df_female['gender'] = 'female'
    df_male['gender'] = 'male'
    df = pd.concat([df_female, df_male], ignore_index=True)
    df.rename(columns={'V': 'valance', 'std(V)': 'std(valance)'}, inplace=True)
    df = df[df.apply(is_valid_post, axis=1)]
    df['week'] = df['week'].apply(get_last_day_of_week)
    df.rename(columns={'week': 'publication_date', 'post': 'content'}, inplace=True)

    id_strings = [f'reddit_{i:06}' for i in range(1, len(df) + 1)]
    df.insert(0, 'id', id_strings)

    metadata_path = os.path.join(output_dir, 'reddit_processed', 'metadata.json')
    corpus_path = os.path.join(output_dir, 'reddit_processed', 'corpus.txt')
    Path(corpus_path).parent.mkdir(parents=True, exist_ok=True)

    if limit:
        max_num_articles_export = min(len(df.index), limit)
    else:
        max_num_articles_export = len(df.index)
    df = df.head(max_num_articles_export)

    ids_and_content = list(zip(df['id'], df['content']))
    with open(corpus_path, 'w') as f:
        for index, (id_string, content) in enumerate(ids_and_content):
            print(f'Exporting Reddit post {index + 1}/{len(ids_and_content)}')
            f.write(f'{id_string}\t{content}\n')

    del df['content']
    df.to_json(metadata_path, orient='records', indent=JSON_INDENT)

    print(f'Success: {max_num_articles_export} Reddit posts written to {corpus_path}')
