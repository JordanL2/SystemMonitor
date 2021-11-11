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
    parser.add_argument('--console', dest='console', action='store_true', default=False, help='output collected data to console rather than writing to database')
    parser.add_argument('--samples', dest='samples', type=int, default=1, help='number of samples to fetch from database')
    args = parser.parse_args()
    action = args.action
    host = args.host
    write_to_console = args.console
    samples = args.samples
    
    if action == 'collect':
        collect(write_to_console)
    elif action == 'fetch':
        fetch(host, samples)

def collect(write_to_console):
    # Get data
    now = datetime.now().strftime(datetime_format)
    collector = Collector()
    data = collector.collect(structured_data=write_to_console)

    if write_to_console:
        # Write data to console
        print(json.dumps(data, cls=DateTimeEncoder, sort_keys=True, indent=4), flush=True)
        
    else:
        # Insert data into DB
        database = Database('localhost')
        database.push(data, now)

def fetch(host, samples):
    database = Database(host)
    res = database.fetch(samples=samples)
    print(json.dumps(res, cls=DateTimeEncoder, sort_keys=True, indent=4), flush=True)


if __name__ == '__main__':
    main()
