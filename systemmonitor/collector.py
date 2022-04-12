#!/usr/bin/python3

from systemmonitor.common import *

from datetime import *
from importlib import import_module
import inspect
import pkgutil
import os.path
import re


class Collector():

    def __init__(self):
        # Load config
        local_config = get_config('localhost')
        self.local_config = local_config
        self.collectors = []
        self.scan_for_collectors([
            os.path.dirname(__file__) + '/collectors',
        ])

    def scan_for_collectors(self, scan_dirs):
        for (_, module_name, _) in pkgutil.iter_modules(scan_dirs):
            package_name = 'systemmonitor.collectors'
            imported_module = import_module("{}.{}".format(package_name, module_name))

            for i in dir(imported_module):
                collector = getattr(imported_module, i)
                if inspect.isclass(collector) and collector != AbstractCollector and issubclass(collector, AbstractCollector):
                    self.collectors.append(collector)

    def collect(self, structured_data=True):
        data = dict()

        # Run all collectors
        for collector in self.collectors:
            collector().collect(data)

        # Custom collection
        if self.local_config is not None and 'custom' in self.local_config:
            for key, custom_config in self.local_config['custom'].items():
                params = custom_config['input']
                if custom_config['method'] == 'file_date_modified':
                    self.data_file_date_modified(data, key, *params)

        # Return data, structured hierarchically if required
        if structured_data:
            return structure_data(data)
        return data


    ### Custom methods ###

    def data_file_date_modified(self, data, key, filename):
        result = cmd("ls -l --time-style=+'%Y-%m-%d %H:%M:%S' {0} | cut -d' ' -f 6,7".format(filename))
        if result == '':
            data[key] = Measurement(None, 'date')
        else:
            dt = datetime.strptime(result, datetime_format)
            data[key] = Measurement(dt, 'date')


class AbstractCollector():

    def collect(self, data):
        raise Exception("Must be overridden")
