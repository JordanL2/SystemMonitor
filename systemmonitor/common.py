#!/usr/bin/python3

from datetime import *
import json
import os.path
import subprocess
import sys
import yaml


datetime_format = '%Y-%m-%d %H:%M:%S'


class Measurement():

    def __init__(self, value, value_type, unit=None, values=None, latest=None):
        self.value = value
        self.type = value_type
        self.unit = unit
        self.values = values
        self.latest = latest

    def json(self):
        res = {
            'value': self.value,
            'type': self.type,
        }
        if self.unit is not None:
            res['unit'] = self.unit
        if self.values is not None:
            res['values'] = dict([(str(k), v) for k, v in self.values.items()])
        if self.latest is not None:
            res['latest'] = self.latest
        return res


class CommandException(Exception):

    def __init__(self, code, error):
        self.code = code
        self.error = error
        super().__init__(self, "Command returned code {} - {}".format(code, error))


class DateTimeEncoder(json.JSONEncoder):

    def _preprocess_date(self, obj):
        if isinstance(obj, (date, datetime, timedelta)):
            return str(obj)
        if isinstance(obj, Measurement):
            return obj.json()
        elif isinstance(obj, dict):
            return {self._preprocess_date(k): self._preprocess_date(v) for k,v in obj.items()}
        elif isinstance(obj, list):
            return [self._preprocess_date(i) for i in obj]
        return obj

    def default(self, obj):
        if isinstance(obj, (date, datetime, timedelta)):
            return str(obj)
        if isinstance(obj, Measurement):
            return obj.json()
        return super().default(obj)

    def iterencode(self, obj, _one_shot=True):
        return super().iterencode(self._preprocess_date(obj), _one_shot)


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
    return {}

def cmd(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8').rstrip("\n")
    stderr = result.stderr.decode('utf-8').rstrip("\n")
    if result.returncode != 0:
        raise CommandException(result.returncode, stderr)
    return stdout

def check_installed(command):
    try:
        cmd("command -v {}".format(command))
    except CommandException as e:
        return False
    return True

def out(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

def err(*messages):
    print(' '.join([str(m) for m in messages]), flush=True, file=sys.stderr)

def fail(*messages):
    err(*messages)
    sys.exit(1)

def structure_data(data):
    structured_data = {}

    for key, value_data in data.items():
        keys = key.split('.')
        p = structured_data
        for k in keys[0:-1]:
            if k not in p:
                p[k] = {}
            p = p[k]

        p[keys[-1]] = value_data

    return structured_data

def flatten_data(data):
    flat_data = {}

    if isinstance(data, Measurement):
        return data
    else:
        for k, v in data.items():
            sublevel = flatten_data(v)
            if isinstance(sublevel, Measurement):
                flat_data[k] = sublevel
            else:
                for sublevel_k, sublevel_v in sublevel.items():
                    flat_data["{}.{}".format(k, sublevel_k)] = sublevel_v

    return flat_data
