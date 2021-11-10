#!/usr/bin/python3

from datetime import *
import json
import mariadb
import os.path
import yaml


def get_config(host):
    config_files = [
        '~/.config/systemmonitor.yml',
        '/usr/local/etc/systemmonitor.yml',
        '/etc/systemmonitor.yml',
    ]
    for config_file in config_files:
        config_file = os.path.expanduser(config_file)
        if os.path.exists(config_file):
            with open(config_file, 'r') as fh:
                config = yaml.load(fh, Loader=yaml.CLoader)
            if host in config:
                return config[host]
            return {}
    raise Exception("Did not find valid config file in: {}".format(', '.join(config_files)))


class DateTimeEncoder(json.JSONEncoder):

    def _preprocess_date(self, obj):
        if isinstance(obj, (date, datetime, timedelta)):
            return str(obj)
        elif isinstance(obj, dict):
            return {self._preprocess_date(k): self._preprocess_date(v) for k,v in obj.items()}
        elif isinstance(obj, list):
            return [self._preprocess_date(i) for i in obj]
        return obj

    def default(self, obj):
        if isinstance(obj, (date, datetime, timedelta)):
            return str(obj)
        return super().default(obj)

    def iterencode(self, obj, _one_shot=True):
        return super().iterencode(self._preprocess_date(obj), _one_shot)
