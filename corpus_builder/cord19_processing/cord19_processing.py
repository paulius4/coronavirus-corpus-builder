import json
import os
import random
from os import listdir
from os.path import isfile, join
from pathlib import Path

import pandas as pd
import pypandoc

from config import JSON_INDENT
from corpus_builder.utilities import replace_linebreaks


def get_authors_and_countries(paper_json):
    names = []
    countries = []
    for author_info in paper_json['metadata']['authors']:
        name = f'{author_info["first"]} {author_info["last"]}'.strip()

        country = ''
        try:
            country = author_info['affiliation']['location']['country'].strip()
        except KeyError:
            pass

        if name and name not in names:
            names.append(name)

        if country and country not in countries:
            countries.append(country)

    return ','.join(names), ','.join(countries)


def process_paper(paper_json):
    all_text = []
    title = paper_json['metadata']['title']
    all_text.append(title)

    sections_seen_abstract = []
    try:
        for paragraph in paper_json['abstract']:
            if paragraph['section'] not in sections_seen_abstract:
                sections_seen_abstract.append(paragraph['section'])
                all_text.append(paragraph['section'])
            all_text.append(paragraph['text'])
    except KeyError:
        pass

    sections_seen_body = []
    for paragraph in paper_json['body_text']:
        if paragraph['section'] not in sections_seen_body:
            sections_seen_body.append(paragraph['section'])
            all_text.append(paragraph['section'])
        all_text.append(paragraph['text'])

    return '\n'.join(all_text)


def generate_cord19_docx_sample(input_dir, output_dir, limit=200):
    if not os.path.isabs(input_dir):
        input_dir = os.path.join(os.getcwd(), input_dir)
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.getcwd(), output_dir)

    pdf_json_dir = join(input_dir, 'document_parses', 'pdf_json')
    pmc_json_dir = join(input_dir, 'document_parses', 'pmc_json')

    pdf_json_files = [join(pdf_json_dir, f) for f in listdir(pdf_json_dir) if
                      isfile(join(pdf_json_dir, f))]
    pmc_json_files = [join(pmc_json_dir, f) for f in listdir(pmc_json_dir) if
                      isfile(join(pmc_json_dir, f))]
    all_json_paths = pdf_json_files + pmc_json_files

    max_num_articles_export = min(len(all_json_paths), limit)

    sampled_json_paths = random.sample(all_json_paths, max_num_articles_export)

    docx_output_dir = join(output_dir, 'cord19_docx_sample/')
    Path(docx_output_dir).mkdir(parents=True, exist_ok=True)

    paper_ids_and_texts = []
    for path in sampled_json_paths:
        with open(path) as fp:
            json_data = json.load(fp)
            paper_id = json_data['paper_id']
            paper_text = process_paper(json_data)
            paper_text = replace_linebreaks(paper_text)
            paper_ids_and_texts.append((paper_id, paper_text))

    num_articles_exported = 0
    for index, (paper_id, paper_text) in enumerate(paper_ids_and_texts):
        print(f'Processing paper {index + 1}/{len(paper_ids_and_texts)}')

        output_txt = os.path.join(docx_output_dir, f'{paper_id}.txt')
        output_docx = os.path.join(docx_output_dir, f'{paper_id}.docx')
        with open(output_txt, "w") as text_file:
            text_file.write(f'{paper_text}\n')
            num_articles_exported += 1
        pypandoc.convert_file(output_txt, 'docx', format='markdown', outputfile=output_docx)
        os.remove(output_txt)
    print(f'Success: {num_articles_exported} .docx files have been saved to {docx_output_dir}')


def process_cord19(input_dir, output_dir, limit=None):
    if not os.path.isabs(input_dir):
        input_dir = os.path.join(os.getcwd(), input_dir)
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.getcwd(), output_dir)

    pdf_json_dir = join(input_dir, 'document_parses', 'pdf_json')
    pmc_json_dir = join(input_dir, 'document_parses', 'pmc_json')

    pdf_json_files = [join(pdf_json_dir, f) for f in listdir(pdf_json_dir) if
                      isfile(join(pdf_json_dir, f))]
    pmc_json_files = [join(pmc_json_dir, f) for f in listdir(pmc_json_dir) if
                      isfile(join(pmc_json_dir, f))]
    all_json_paths = pdf_json_files + pmc_json_files

    cord_metadata_path = join(input_dir, 'metadata.csv')

    df_metadata = pd.read_csv(cord_metadata_path, low_memory=False)

    corpus_output_dir = join(output_dir, 'cord19_processed')
    Path(corpus_output_dir).mkdir(parents=True, exist_ok=True)
    corpus_output_path = join(corpus_output_dir, 'corpus.txt')
    metadata_output_path = join(corpus_output_dir, 'metadata.json')

    if limit:
        max_num_articles_export = min(len(all_json_paths), limit)
    else:
        max_num_articles_export = len(all_json_paths)

    metadata_output = []
    lines_in_batch = []
    for index, path in enumerate(all_json_paths[:max_num_articles_export]):
        print(f'Processing CORD-19 article {index + 1}/{max_num_articles_export}')

        with open(path) as fp:
            paper_json = json.load(fp)

        paper_text = process_paper(paper_json)
        paper_sha1 = paper_json['paper_id']

        paper_text = replace_linebreaks(paper_text)
        authors_and_countries = get_authors_and_countries(paper_json)

        try:
            paper_info = \
                df_metadata.loc[df_metadata['sha'].str.contains(paper_sha1, na=False), :].to_dict('records')[0]
            paper_metadata = {'id': paper_json['paper_id'],
                              'title': paper_json['metadata']['title'],
                              'author': authors_and_countries[0],
                              'location': authors_and_countries[1],
                              'journal': paper_info['journal'],
                              'doi': paper_info['doi'],
                              'url': paper_info['url'],
                              'publication_date': paper_info['publish_time']}
        except IndexError:
            paper_metadata = {'id': paper_json['paper_id'],
                              'title': paper_json['metadata']['title'],
                              'author': authors_and_countries[0],
                              'location': authors_and_countries[1],
                              'journal': None,
                              'doi': None,
                              'url': None,
                              'publication_date': None}

        metadata_output.append(paper_metadata)
        lines_in_batch.append(f'{paper_sha1}\t{paper_text}')

        if (index % 1000 == 0 and index != 0) or index == len(all_json_paths) - 1:
            print(f'Index {index + 1}/{len(all_json_paths)} - writing a batch of articles')
            text_to_append = '\n'.join(lines_in_batch)

            with open(corpus_output_path, 'a') as fh:
                fh.write(text_to_append)

            lines_in_batch = []

    with open(metadata_output_path, 'w') as f:
        print('Writing metadata')
        json.dump(metadata_output, f, indent=JSON_INDENT, sort_keys=True)

    print(f'Success: {max_num_articles_export} CORD-19 articles written to {corpus_output_dir}')
