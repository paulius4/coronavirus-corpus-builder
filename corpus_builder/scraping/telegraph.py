import json
from urllib.parse import urljoin

import mongoengine
import requests
import trafilatura
from bs4 import BeautifulSoup
from dateutil.parser import parse
from mongoengine import connect
from newspaper import Article

from config import MONGO_DB_NAME, DB_HOST, DB_PORT
from corpus_builder.database.database import Post, Source
from corpus_builder.scraping.headers import BASIC_HEADERS
from corpus_builder.utilities import sleep_for

ROOT_URL = 'https://www.telegraph.co.uk/'

NUM_PAGES_TO_CHECK = 1000


def get_current_page_urls(page_num):
    PAGE_URL = 'https://www.telegraph.co.uk/coronavirus/page-{page_num}/'
    page_url = PAGE_URL.format(page_num=page_num)
    print(f'Visiting {page_url}')
    response = requests.request('GET', page_url, headers=BASIC_HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    article_urls = set()
    for a_tag_article in soup.select('a.list-headline__link'):
        article_url = urljoin(ROOT_URL, a_tag_article['href'])
        article_urls.add(article_url)

    print(f'Extracted {len(article_urls)} article URLs from this page')

    return list(article_urls)


def get_all_article_urls_pagination(limit=None, wait=None):
    print(f'Starting to collect article URLs')

    all_urls = []
    for page_num in range(1, NUM_PAGES_TO_CHECK + 2):
        print(f'Processing page {page_num}')
        current_page_urls = get_current_page_urls(page_num)
        all_urls.extend(current_page_urls)
        print(f'Total URLs: {len(all_urls)}')
        if limit and len(all_urls) >= limit:
            break
        if wait:
            sleep_for(wait)

    print(f'Collection of article URLs completed. {len(all_urls)} URLs collected.')
    return all_urls


def scrape_articles(article_urls, limit=None, wait=None):
    connect(MONGO_DB_NAME, host=DB_HOST, port=DB_PORT)
    print('Starting to scrape telegraph.co.uk articles')

    num_articles_saved = 0
    max_num_articles_process = min(len(article_urls), limit)
    for index, article_url in enumerate(article_urls):
        print(f'Processing article {index + 1}/{max_num_articles_process}')
        print(f'Visiting {article_url}')

        try:
            response = requests.request('GET', article_url, headers=BASIC_HEADERS)
        except requests.exceptions.TooManyRedirects as e:
            print(e)
            print(f'Skipping article {index + 1}/{len(article_urls)}')
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        html = soup.encode_contents()

        article_n3k = Article(article_url)
        article_n3k.set_html(html)
        article_n3k.parse()

        article_tf_json = trafilatura.extract(html, output_format='json', with_metadata=True)
        try:
            article_tf = json.loads(article_tf_json)
        except TypeError as e:
            print(e)
            print(f'Skipping article {index + 1}/{len(article_urls)}')
            continue

        title = article_n3k.meta_data['og']['title']
        try:
            description = article_n3k.meta_data['og']['description']
        except KeyError:
            description = None
        date = str(parse(article_tf['date']).date())
        content = article_tf['text']
        author = article_tf['author']
        tags = article_tf['tags'].split(',')

        post = Post(source=Source.TELEGRAPH.name.lower(),
                    url=article_url,
                    content=content,
                    id_custom=index + 1,
                    title=title,
                    author=author,
                    date=date,
                    description=description,
                    tags=tags)
        try:
            post.save()
            num_articles_saved += 1
        except mongoengine.errors.NotUniqueError as e:
            print(f'Skipping article {index}! Exception: {e}')

        if limit and index >= limit - 1:
            break
        if wait:
            sleep_for(wait)

    print(f'Collection of articles completed. {num_articles_saved} articles saved to MongoDB.')


def scrape_telegraph(limit=None, wait=None):
    article_urls = get_all_article_urls_pagination(limit, wait)
    scrape_articles(article_urls, limit, wait)
