import json
import math
from urllib.parse import urljoin

import mongoengine
import requests
import trafilatura
from bs4 import BeautifulSoup
from mongoengine import connect
from newspaper import Article

from config import MONGO_DB_NAME, DB_HOST, DB_PORT
from corpus_builder.database.database import Source, Post
from corpus_builder.scraping.headers import BASIC_HEADERS
from corpus_builder.utilities import sleep_for

MAIN_CATEGORY_URL = 'https://www.theguardian.com/world/coronavirus-outbreak/all'
ROOT_URL = 'https://www.theguardian.com'
NUM_ARTICLES_PER_PAGE = 20


def get_num_pages():
    print('Getting the number of pages in pagination')
    response = requests.request('GET', MAIN_CATEGORY_URL, headers=BASIC_HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    pagination_legend_span = soup.select_one('span.pagination__legend')
    num_articles = int(pagination_legend_span.text.split()[1].replace(',', ''))
    num_pages = math.ceil(num_articles / NUM_ARTICLES_PER_PAGE)
    print(f'Found {num_pages} pages')
    return num_pages


def get_urls_in_page(page_num):
    page_url_template = 'https://www.theguardian.com/world/coronavirus-outbreak?page={page_num}'
    page_url = page_url_template.format(page_num=page_num)
    print(f'Visiting {page_url}')
    response = requests.request('GET', page_url, headers=BASIC_HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    article_urls = []
    for a_tag_article in soup.select('a.fc-item__link'):
        article_url = a_tag_article['href']
        if not article_url.startswith(ROOT_URL):
            article_url = urljoin(ROOT_URL, a_tag_article['href'])
        article_urls.append(article_url)

    print(f'Extracted {len(article_urls)} article URLs from this page')
    return article_urls


def get_all_article_urls_pagination(limit=None, wait=None):
    num_pages = get_num_pages()
    print(f'Starting to collect article URLs: {num_pages} pages to process')

    all_urls = []
    for page_num in range(1, num_pages + 1):
        print(f'Processing page {page_num}')
        current_page_urls = get_urls_in_page(page_num)
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
    print('Starting to scrape theguardian.com articles')

    num_articles_saved = 0
    max_num_articles_process = min(len(article_urls), limit)
    for index, article_url in enumerate(article_urls):
        print(f'Processing article {index + 1}/{max_num_articles_process}')
        print(f'Visiting {article_url}')

        response = requests.request('GET', article_url, headers=BASIC_HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')
        html = soup.encode_contents()

        article_n3k = Article(article_url)
        article_n3k.set_html(html)
        article_n3k.parse()

        article_tf_json = trafilatura.extract(html, output_format='json', with_metadata=True)
        try:
            article_tf = json.loads(article_tf_json)
        except TypeError as e:
            print(f'Skipping article {index + 1}! Exception: {e}')
            continue

        content = article_tf['text']
        tags = article_tf['tags'].split(',')
        date = article_tf['date']
        author = article_tf['author']
        title = article_tf['title']
        try:
            description = article_n3k.meta_data['og']['description']
        except KeyError:
            description = None

        post = Post(source=Source.GUARDIAN.name.lower(),
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


def scrape_guardian(limit=None, wait=None):
    article_urls = get_all_article_urls_pagination(limit, wait)
    scrape_articles(article_urls, limit, wait)
