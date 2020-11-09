#!/usr/bin/python3

import mariadb
import yaml


def get_config(host):
    config_file = '/usr/local/etc/systemmonitor.yml'
    with open(config_file, 'r') as fh:
        config = yaml.load(fh)
    return config[host]
