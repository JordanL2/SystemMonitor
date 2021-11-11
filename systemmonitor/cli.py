#!/usr/bin/python3

from systemmonitor.common import *
from systemmonitor.collector import Collector
from systemmonitor.database import Database

import argparse
from datetime import *
import json


def main():
    parser = argparse.ArgumentParser(prog='systemmonitor')

    parser.add_argument('action', choices=['collect', 'fetch'], help='action to perform')
    parser.add_argument('host', nargs='?', help='host to fetch data for')
    parser.add_argument('--output', dest='output', choices=['database', 'json'], default='json', help='where the collected data is output to (default: json)')
    parser.add_argument('--samples', dest='samples', type=int, default=1, help='number of samples to fetch from database (default: 1)')

    args = parser.parse_args()

    action = args.action
    host = args.host
    output = args.output
    samples = args.samples

    if action == 'collect':
        collect(output)
    elif action == 'fetch':
        fetch(host, samples)
    else:
        fail("Not recognised action:", action)

def collect(output):
    now = datetime.now().strftime(datetime_format)
    collector = Collector()
    need_structured_data = output != 'database'
    data = collector.collect(structured_data=need_structured_data)

    if output == 'json':
        # Write data to console in JSON format
        out(json.dumps(data, cls=DateTimeEncoder, sort_keys=True, indent=4))
    elif output == 'database':
        # Insert data into DB
        database = Database('localhost')
        database.push(data, now)
    else:
        fail("Not recognised output:", output)

def fetch(host, samples):
    database = Database(host)
    res = database.fetch(samples=samples)
    out(json.dumps(res, cls=DateTimeEncoder, sort_keys=True, indent=4))


if __name__ == '__main__':
    main()
