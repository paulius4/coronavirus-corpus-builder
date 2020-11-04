import time
from random import randrange

import unidecode as unidecode

from config import PARAGRAPH_SEPARATOR


def replace_linebreaks(content):
    content = content.replace('\r', '').replace('\n', ' <p> ')
    return content.replace(f'{PARAGRAPH_SEPARATOR}  {PARAGRAPH_SEPARATOR}', PARAGRAPH_SEPARATOR).replace('  ', ' ')


def decode_unicode(content):
    return unidecode.unidecode(content)


def decode_unicode_in_dict(dictionary):
    dictionary = {k: (decode_unicode(v) if isinstance(v, str) else v) for k, v in dictionary.items()}
    return dictionary


def sleep_for(lower_boundary, upper_boundary=None):
    if upper_boundary is not None:
        time_interval = randrange(lower_boundary, upper_boundary)
    else:
        time_interval = lower_boundary

    print(f'Sleeping for {time_interval} seconds...')
    time.sleep(time_interval)


def remove_none_dict_values(dictionary):
    new_dictionary = {}
    keys_to_keep = ['author', 'id', 'date']

    for k, v in dictionary.items():
        if k not in keys_to_keep:
            if v is None:
                continue
            if v == '':
                continue
            if type(v) is list and len(v) == 0:
                continue

        new_dictionary[k] = v

    return new_dictionary
