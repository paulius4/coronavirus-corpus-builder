import json
from urllib.parse import urljoin

import mongoengine
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from mongoengine import connect
from newspaper import Article

from config import MONGO_DB_NAME, DB_HOST, DB_PORT
from corpus_builder.database.database import Source, Post
from corpus_builder.scraping.headers import BASIC_HEADERS
from corpus_builder.utilities import sleep_for

MAIN_CATEGORY_URL = 'https://www.weforum.org/agenda/archive/covid-19'
ROOT_URL = 'https://www.weforum.org'


def get_num_pages():
    print('Getting the number of pages in pagination')
    response = requests.request('GET', MAIN_CATEGORY_URL, headers=BASIC_HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    pagination_info_div = soup.select_one('div.pagination__page-info')
    num_pages = int(pagination_info_div.text[2:])
    print(f'Found {num_pages} pages')
    return num_pages


def get_urls_in_page(page_num):
    page_url_template = 'https://www.weforum.org/agenda/archive/covid-19?page={page_num}'
    page_url = page_url_template.format(page_num=page_num)
    print(f'Visiting {page_url}')
    response = requests.request('GET', page_url, headers=BASIC_HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    article_urls = []
    for a_tag_article in soup.select('article:not(.tout--transformation-map) > a.tout__link'):
        article_url = a_tag_article['href']
        if not article_url.startswith(ROOT_URL):
            article_url = urljoin(ROOT_URL, a_tag_article['href'])
        if article_url.startswith('https://www.weforum.org/videos/'):
            continue
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
    print('Starting to scrape weforum.org articles')

    num_articles_saved = 0
    max_num_articles_process = min(len(article_urls), limit)
    for index, article_url in enumerate(article_urls):
        print(f'Processing article {index + 1}/{max_num_articles_process}')
        print(f'Visiting {article_url}')

        response = requests.request('GET', article_url, headers=BASIC_HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')
        html = soup.encode_contents()

        # The library doesn't extract text from weforum.org correctly (returns '\n'). This is a workaround.
        try:
            article_text = soup.find('div', class_='article-body').text
        except AttributeError:
            try:
                article_text = soup.find('section', class_='article-story__body').text
            except AttributeError as e:
                print(f'Skipping article {index + 1}! Exception: {e}')
                continue

        article_text = '\n'.join([line.strip() for line in article_text.split('\n')
                                  if line.strip() and 'We use cookies to improve your' not in line])

        article_n3k = Article(article_url)
        article_n3k.set_html(html)
        article_n3k.parse()
        article_n3k.set_text(article_text)

        try:
            matched_lines = [line for line in str(soup.html).split('\n') if line.startswith('{"@context"')]
            metadata = json.loads(matched_lines[0])
        except Exception as e:
            print(f'Skipping article {index + 1}! Exception: {e}')
            continue

        content = article_n3k.text
        date = str(parse(metadata['dateCreated']).date())
        if metadata['creator']:
            author = metadata['creator'][0]
        else:
            author = None
        category = metadata['articleSection']
        keywords = metadata['keywords']
        description = article_n3k.meta_data['og']['description']
        title = article_n3k.meta_data['og']['title']

        post = Post(source=Source.WEFORUM.name.lower(),
                    url=article_url,
                    content=content,
                    id_custom=index + 1,
                    title=title,
                    author=author,
                    date=date,
                    description=description,
                    category=category,
                    keywords=keywords)
        try:
            post.save()
            num_articles_saved += 1
        except mongoengine.errors.NotUniqueError as e:
            print(f'Skipping article {index + 1}! Exception: {e}')

        if limit and index >= limit - 1:
            break
        if wait:
            sleep_for(wait)

    print(f'Collection of articles completed. {num_articles_saved} articles saved to MongoDB.')


def scrape_weforum(limit=None, wait=None):
    article_urls = get_all_article_urls_pagination(limit, wait)
    scrape_articles(article_urls, limit, wait)
