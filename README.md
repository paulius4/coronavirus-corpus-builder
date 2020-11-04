# Corpus Builder for Coronavirus Texts 
## Table of Contents
   * [Corpus Builder for Coronavirus Texts](#corpus-builder-for-coronavirus-texts)
      * [Table of Contents](#table-of-contents)
      * [Requirements](#requirements)
      * [Functionality](#functionality)
         * [Article Scraping](#article-scraping)
            * [Instructions](#instructions)
               * [Usage: scrape_articles.py](#usage-scrape_articlespy)
               * [Usage: export_articles.py](#usage-export_articlespy)
         * [CORD-19 Processing](#cord-19-processing)
            * [Instructions](#instructions-1)
               * [Usage: process_cord.py](#usage-process_cordpy)
         * [Reddit Processing](#reddit-processing)
            * [Instructions](#instructions-2)
               * [Usage:process_reddit.py](#usageprocess_redditpy)
         * [Tweet Hydration](#tweet-hydration)
            * [Instructions](#instructions-3)
               * [Usage: hydrate_tweets.py](#usage-hydrate_tweetspy)

## Requirements
* Python 3.6+
* Python packages specified in `requirements.txt`
* MongoDB

## Functionality
The code in this repository is intended to be used by running the Python scripts in the `scripts` directory.
The following scripts are available:
* `export_articles.py`
* `hydrate_tweets.py`
* `process_cord19.py`
* `process_reddit.py`
* `scrape_articles.py`

Their functionality is described in the sections below.

### Article Scraping
The `scrape_articles.py` script can scrape the following sources:
* [GOV.UK News](https://www.gov.uk/search/news-and-communications?level_one_taxon=5b7b9532-a775-4bd2-a3aa-6ce380184b6c&order=updated-newest)
* [The Telegraph](https://www.telegraph.co.uk/coronavirus/)
* [The Guardian](https://www.theguardian.com/world/coronavirus-outbreak/all)
* [The World Economic Forum](https://www.weforum.org/agenda/archive/covid-19)
* [The Sun](https://www.thesun.co.uk/topic/coronavirus/)

The articles are saved in a MongoDB collection. They can then be exported by running `export_articles.py`.

#### Instructions
1. Ensure that MongoDB is installed  ([installation instructions](https://docs.mongodb.com/manual/installation/)).
2. Ensure the mongodb service is running: ` sudo service mongod start`

##### Usage: `scrape_articles.py`
```
usage: scrape_articles.py [-h] [-l LIMIT] [-w WAIT] source

Scrape coronavirus-related articles

positional arguments:
  source                A source to scrape articles from. Valid options:
                        gov_uk_news, telegraph, guardian, sun, weforum

optional arguments:
  -h, --help            show this help message and exit
  -l LIMIT, --limit LIMIT
                        How many articles to scrape at most (default: all
                        available)
  -w WAIT, --wait WAIT  Wait time between requests (default: 3)
```
Example:
```
python scrape_articles.py guardian -l 100 -w 3
```

##### Usage: `export_articles.py`
```
usage: export_articles.py [-h] [-l LIMIT] [-o OUTPUT_DIR] [-d] source

Export articles collected by scrape_articles.py

positional arguments:
  source                Export articles collected from this source. Valid
                        options: gov_uk_news, telegraph, guardian, sun,
                        weforum

optional arguments:
  -h, --help            show this help message and exit
  -l LIMIT, --limit LIMIT
                        How many articles to export most (default: all
                        available)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory where to save the articles (default: current
                        working directory)
  -d, --docx            Export a sample of articles in .docx format (default:
                        no). Default limit for .docx: 200

```
Example:
```
python export_articles.py telegraph -l 50 -o extracted_articles
```

### CORD-19 Processing
The `process_cord19.py` script can output the CORD-19 dataset in a standardised JSON format.

#### Instructions
1. Download the CORD-19 dataset ([download link](https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/historical_releases/cord-19_2020-10-28.tar.gz)).
2. Extract the downloaded archive. You should get a directory with a date for its name, e.g. `2020-10-28`.
It should contain the following files: `cord_19_embeddings.tar.gz`, `document_parses.tar.gz`, and `metadata.csv`.
3. Extract the archive `document_parses.tar.gz`. 
In the resulting directory, there will be two child directories: `pdf_json` and `pmc_json`.
4. The top-level directory (`2020-10-28` at the time of writing) needs to have the following layout:
    ```
    ├───document_parses
    │   ├───pdf_json
    │   │      ...
    │   └───pmc_json
    │   │      ...
    ├───metadata.csv
    ```
    `metadata.csv` and the JSON files in `pdf_json` and `pmc_json` will be used to produce the output.

5. The top-level directory (`2020-10-28`) should be passed as the positional argument `-i` to the `process_cord19.py` script.

##### Usage: `process_cord.py`
```
usage: process_cord19.py [-h] [-o OUTPUT_DIR] [-l LIMIT] [-d] input_dir

Output the CORD-19 dataset in a standard format

positional arguments:
  input_dir             Directory where the source CORD-19 dataset is stored
                        (see README.md)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory where to save the articles (default: current
                        working directory)
  -l LIMIT, --limit LIMIT
                        How many articles to export at most (default: all
                        available)
  -d, --docx            Export a sample of articles in .docx format (default:
                        no). Default limit for .docx: 200
```
Example:
```
python process_cord19.py /home/admin/Downloads/2020-10-28 -o cord19_articles
```

### Reddit Processing
The `process_cord19.py` script can output a dataset of coronavirus-related posts in a JSON format.

#### Instructions
1. Download the Reddit dataset corresponding to [this paper](https://arxiv.org/abs/2008.05713)
([dataset download link](https://github.com/ellarabi/covid19-demography/tree/master/data.gender.vad.scores)).
2. Two files are needed: `data.F.v.csv` and `data.M.v.csv`. Place them in the same directory (e.g. `reddit_data`)
3. The top-level directory (`reddit_dataset`) should be passed as the positional argument `-i` to the `process_reddit.py` script.

##### Usage: `process_reddit.py`
```
usage: process_reddit.py [-h] [-o OUTPUT_DIR] [-l LIMIT] input_dir

Output the Reddit dataset in a standard format

positional arguments:
  input_dir             Directory where the source Reddit dataset is stored
                        (see README.md)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory where to save the posts (default: current
                        working directory)
  -l LIMIT, --limit LIMIT
                        How many posts to export at most (default: all
                        available)
```

Example:
```
python process_reddit.py /home/admin/Downloads/reddit_data  -o reddit_posts -l 500
```

### Tweet Hydration
The `process_cord19.py` script can output a dataset of coronavirus-related posts in a JSON format.

#### Instructions
1. Apply for a Twitter developer account. This is needed to gain access to the Twitter API.
Please review their [Developer Agreement and Policy](https://developer.twitter.com/en/developer-terms/agreement-and-policy)
and ensure your use case does not break their rules.
You can apply for a developer account [here](https://developer.twitter.com/en/apply-for-access).
2. Configure `twarc` ([instructions](https://github.com/DocNow/twarc)) with your Twitter API credentials.
3. Download the [Coronavirus (COVID-19) Tweets Dataset](https://ieee-dataport.org/open-access/coronavirus-covid-19-tweets-dataset#files).
This source dataset covers the date range from 2020-03-20 to 2020-11-02 at the time of writing.
The dataset is provided as a collection of distinct .csv and .zip files.
The .zip files need to be extracted, and all of the resulting .csv files need to moved into the same directory (e.g. `tweets_dataport`).
The .zip archives can be deleted.
4. Download the [TweetsCOV19 Dataset](https://zenodo.org/record/3871753).
This source dataset covers the date range of October 2019 until April 2020.
It is provided as a single .gz file (`TweetsCOV19.tsv.gz`).
The archive needs to be extracted, and the resulting `TweetsCOV19.tsv` file should be moved into a new directory (e.g. `tweets_cov19`).
This dataset can be combined with the previous dataset, mentioned in step 3, to allow us to have a collection of source tweet IDs
that span a wider data range. The recommended approach is to use `tweets_cov19` for the date range from October 2019
to 20 March 2020, and for the dates from 20 March 2020 onwards, use `tweets_dataport`.
5. Update the settings in `corpus_builder/tweet_hydration/settings.py` and set the paths there as needed.
6. Configure and run the following two preprocessing scripts:
`corpus_builder/tweet_hydration/preprocess_tweets_cov19.py` and `corpus_builder/tweet_hydration/preprocess_tweets_dataport.py`
7. The main script `hydrate_tweets.py` can then be run without any command-line parameters.

##### Usage: `hydrate_tweets.py`
```
usage: hydrate_tweets.py [-h]

Download information about tweet IDs provided (settings found in
corpus_builder/tweet_hydration/settings.py)

optional arguments:
  -h, --help  show this help message and exit
```

Example:
```
python hydrate_tweets.py
```