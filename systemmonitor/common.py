#!/usr/bin/python3

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
        try:
            with open(config_file, 'r') as fh:
                config = yaml.load(fh)
            return config[host]
        except Exception:
            pass
    raise Exception("Did not find valid config file in: {}".format(', '.join(config_files)))
