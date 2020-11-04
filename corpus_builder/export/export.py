import json
import os
import random
from os.path import join
from pathlib import Path

import pypandoc
from mongoengine import *

from config import JSON_INDENT, DB_PORT, MONGO_DB_NAME
from corpus_builder.database.database import Post
from corpus_builder.utilities import remove_none_dict_values, decode_unicode, replace_linebreaks

ID_FORMAT = '{ID:05d}_{SOURCE}'
ID_FORMAT_TWITTER = '{ID:05d}_{SOURCE}_{USERNAME}'
JSON_FILENAME = '{ID:05d}_{SOURCE}.json'
JSON_FILENAME_TWITTER = '{ID:05d}_{SOURCE}_{USERNAME}.json'


def pop_article_content(article):
    content = article.pop('content')
    content = decode_unicode(content)
    content = replace_linebreaks(content)
    return content


def prepare_article_dict(article):
    prepared_article = article.to_mongo()
    prepared_article = remove_none_dict_values(prepared_article)
    del prepared_article['_id']
    del prepared_article['scrape_datetime']
    prepared_article['id'] = prepared_article.pop('id_custom')
    return prepared_article


def export_articles(source, output_dir, limit=None, db_name=MONGO_DB_NAME):
    connect(db_name, host='localhost', port=DB_PORT)
    articles = Post.objects.filter(source=source.name.lower())

    articles_json = []
    articles_content = []

    if limit:
        max_num_articles_export = min(len(articles), limit)
    else:
        max_num_articles_export = len(articles)

    for index, article in enumerate(articles[:max_num_articles_export]):
        print(f'Processing article {index + 1}/{max_num_articles_export}')
        prepared_article = prepare_article_dict(article)
        content = pop_article_content(prepared_article)

        articles_json.append(prepared_article)
        article_id = ID_FORMAT.format(ID=prepared_article['id'], SOURCE=prepared_article['source'])
        articles_content.append(f'{article_id}\t{content}\n')

    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.getcwd(), output_dir)

    corpus_filepath = join(output_dir, source.name.lower(), 'corpus.txt')
    Path(corpus_filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(corpus_filepath, 'w') as f:
        for article in articles_content:
            f.write(f'{article}')

    json_filepath = join(output_dir, source.name.lower(), 'metadata.json')
    Path(json_filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(json_filepath, 'w') as f:
        json.dump(articles_json, f, indent=JSON_INDENT, sort_keys=True)

    print(f'Success: {max_num_articles_export} articles from {source.name.capitalize()} '
          f'have been saved to {Path(corpus_filepath).parent}')


def export_sample_docx(source, output_dir, limit=200, db_name=MONGO_DB_NAME):
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.getcwd(), output_dir)
    docx_output_dir = join(output_dir, f'{source.name.lower()}_docx_sample/')
    Path(docx_output_dir).mkdir(parents=True, exist_ok=True)

    connect(db_name, host='localhost', port=DB_PORT)
    all_articles = Post.objects.filter(source=source.name.lower())
    if limit > len(all_articles):
        limit = len(all_articles)
    articles = random.sample(list(all_articles), limit)

    for index, post in enumerate(articles):
        print(f'Processing post {index}/{len(articles)}')
        prepared_article = prepare_article_dict(post)
        post_id = ID_FORMAT.format(ID=prepared_article['id'], SOURCE=prepared_article['source'])
        content = pop_article_content(prepared_article)
        content = f'{content}'

        output_txt = join(docx_output_dir, f'{post_id}.txt')
        output_docx = join(docx_output_dir, f'{post_id}.docx')
        with open(output_txt, "w") as text_file:
            text_file.write(f'{content}\n')
        pypandoc.convert_file(output_txt, 'docx', format='markdown', outputfile=output_docx)
        os.remove(output_txt)

    print(f'Success: {limit} {source.name.lower()} .docx files have been saved to {docx_output_dir}')
