#!/usr/bin/python3

from systemmonitor.common import *

from datetime import *
import json
import sys


datetime_format = '%Y-%m-%d %H:%M:%S'


class MonitorApi():

    def __init__(self, host):
        # Load config
        host_config = get_config(host)

        self.db_user = host_config['db']['read']['user']
        self.db_pass = host_config['db']['read']['pass']
        self.db_host = host_config['db']['host']
        self.db_schema = host_config['db']['schema']

    def get(self, samples=None, cleanup=True):
        self.connect()
        
        cur = self.connection.cursor()

        earliest = None
        second_earliest = None
        if samples is not None:
            if samples < 1:
                raise Exception("Number of samples needs to be at least one")
            cur.execute("SELECT distinct(taken) FROM measurements ORDER BY taken desc LIMIT ?", (samples + 1,))
            count = 0
            for (date,) in cur:
                second_earliest = earliest
                earliest = date
                count += 1
            if count <= samples:
                raise Exception("There aren't enough samples in the database")
        else:
            raise Exception("Need to specify number of samples")

        if second_earliest is None:
            raise Exception("Not enough samples - there needs to be at least two in the database")

        cur.execute("SELECT taken, measurement, value_type, value, unit FROM measurements WHERE taken >= ? OR (taken = ? AND value_type = '%s') ORDER BY taken",
            (second_earliest, earliest,))

        data = {}

        for (taken, measurement, value_type, value, unit) in cur:
            category = measurement.split('.')

            pointer = data
            for cat in category:
                if cat not in pointer:
                    pointer[cat] = {}
                pointer = pointer[cat]

            pointer['type'] = value_type

            if 'values' not in pointer:
                pointer['values'] = {}

            if value_type in ('%', 'raw'):
                pointer['values'][taken] = float(value)

            elif value_type == '%s':
                if 'raw' not in pointer:
                    pointer['raw'] = {}
                pointer['raw'][taken] = float(value)
                if len(pointer['raw'].keys()) > 1:
                    previous_time = list(pointer['raw'].keys())[-2]
                    delta_seconds = (taken - previous_time).total_seconds()
                    pointer['values'][taken] = (float(value) - pointer['raw'][previous_time]) / delta_seconds

            elif value_type in ('bytes'):
                pointer['values'][taken] = int(value)

            elif value_type == 'bool':
                pointer['values'][taken] = (value == 'True')

            elif value_type == 'date':
                if value == '':
                    pointer['values'][taken] = None
                else:
                    pointer['values'][taken] = datetime.strptime(value, datetime_format)

            elif value_type == 'string':
                pointer['values'][taken] = value

            else:
                raise Exception("Invalid type: {}".format(value_type))

            if unit is not None:
                if 'unit' in pointer and pointer['unit'] != unit:
                    raise Exception("Varying unit not supported")
                pointer['unit'] = unit
        
        self.disconnect()

        if cleanup:
            self.cleanup(data)

        return data;

    def cleanup(self, data):
        if 'type' in data and isinstance(data['type'], str):
            if 'raw' in data:
                del data['raw']
        else:
            for k in data:
                self.cleanup(data[k])

    def connect(self):
        try:
            conn = mariadb.connect(
                user = self.db_user,
                password = self.db_pass,
                host = self.db_host,
                database = self.db_schema
            )
        except mariadb.Error as e:
            print(f"Error connecting: {e}")
            sys.exit(1)
        self.connection = conn

    def disconnect(self):
        self.connection.close()


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


### ENTRY POINT ###

def main():
    host = 'localhost'
    if len(sys.argv) > 1:
        host = sys.argv[1]

    samples = 1
    if len(sys.argv) > 2:
        samples = int(sys.argv[2])

    m = MonitorApi(host)
    res = m.get(samples=samples)
    print(json.dumps(res, cls=DateTimeEncoder, sort_keys=True, indent=4))


if __name__ == '__main__':
    main()
