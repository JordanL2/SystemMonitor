#!/usr/bin/python3

from datetime import *
import json
import mariadb
import os.path
import yaml
import sys
import subprocess


class CommandException(Exception):

    def __init__(self, code, error):
        self.code = code
        self.error = error
        super().__init__(self, "Command returned code {} - {}".format(code, error))


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
    
def err(*messages):
    print(' '.join([str(m) for m in messages]), flush=True, file=sys.stderr)
    
def structure_data(data):
    structured_data = {}
    
    for key, value_data in data.items():
        keys = key.split('.')
        p = structured_data
        for k in keys[0:-1]:
            if k not in p:
                p[k] = {}
            p = p[k]

        p[keys[-1]] = {}
        value = value_data[0]
        value_type = value_data[1]
        unit = None
        if len(value_data) == 3:
            unit = value_data[2]
        
        if type(value) == dict:
            p[keys[-1]]['values'] = value
        else:
            p[keys[-1]]['value'] = value
        p[keys[-1]]['type'] = value_type
        if unit is not None:
            p[keys[-1]]['unit'] = unit
    
    return structured_data

def flatten_data(data):
    flat_data = {}

    if 'type' in data and type(data['type']) == str:
        unit = None
        if 'unit' in data:
            unit = data['unit']
        if 'value' in data:
            return {
                'value': data['value'],
                'type': data['type'],
                'unit': unit,
            }
        elif 'values' in data:
            latest = sorted(list(data['values'].keys()))[-1]
            return {
                'value': data['values'][latest],
                'type': data['type'],
                'unit': unit,
                'latest': latest,
            }
    else:
        for k, v in data.items():
            sublevel = flatten_data(v)
            if 'type' in sublevel and type(sublevel['type']) == str:
                flat_data[k] = sublevel
            else:
                for sublevel_k, sublevel_v in sublevel.items():
                    flat_data["{}.{}".format(k, sublevel_k)] = sublevel_v

    return flat_data
