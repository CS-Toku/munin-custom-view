
from collections import namedtuple
import os.path
import re
import yaml

MachineTuple = namedtuple('MachineTuple', ['domain', 'host'])


def split_domainhost(dh):
    if ';' in dh:
        d, h = dh.split(';', 1)
    else:
        d, h = dh, dh

    return MachineTuple(d, h if h else None)


def load_default_options(module_filepath):
    filepath = os.path.dirname(module_filepath) + '/option.yaml'
    try:
        yaml_obj = yaml.load(open(filepath, 'r'))
    except Exception:
        yaml_obj = {}
    if not isinstance(yaml_obj, dict):
        yaml_obj = {}
    return yaml_obj


def is_glob_pattern(pattern):
    cnt = pattern.count('*')
    if cnt == 1:
        return True
    elif cnt == 0:
        return False
    else:
        raise ValueError('Many Wildcard...')


def glob_match(pattern, target_list):
    re_pattern = pattern.replace('.', '\\.').replace('*', '.*')+'$'
    prog = re.compile(re_pattern)
    return [t for t in target_list if prog.match(t) is not None]




