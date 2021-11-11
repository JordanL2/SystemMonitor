#!/usr/bin/python3

import argparse
from datetime import *
import json
from systemmonitor.common import *
from systemmonitor.collector import Collector
from systemmonitor.database import Database


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
    
    #print(action, host, write_to_console, samples)
    if action == 'collect':
        collect(write_to_console)
    elif action == 'fetch':
        fetch(host, samples)

def collect(write_to_console):
    # Get data
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    collector = Collector()
    data = collector.collect(structured_data=write_to_console)

    if write_to_console:
        # Write data to console
        print(json.dumps(data, cls=DateTimeEncoder, sort_keys=True, indent=4), flush=True)
        
    else:
        # Insert data into DB
        db_user = collector.local_config['db']['push']['user']
        db_pass = collector.local_config['db']['push']['pass']
        db_host = collector.local_config['db']['host']
        db_schema = collector.local_config['db']['schema']
    
        # Get connection
        try:
            conn = mariadb.connect(
                user = db_user,
                password = db_pass,
                host = db_host,
                database = db_schema
            )
        except mariadb.Error as e:
            err(f"Error connecting: {e}")
            sys.exit(1)
    
        conn.autocommit = False
        cur = conn.cursor()
    
        # Insert each row into the DB
        for key, value in data.items():
            unit = None
            if len(value) == 3:
                unit = value[2]
            try:
                cur.execute("INSERT INTO measurements (taken, measurement, value_type, value, unit) VALUES (?, ?, ?, ?, ?)", (now, key, value[1], str(value[0]), unit))
            except mariadb.Error as e:
                err(f"Error inserting data: {e}")
                conn.close()
                sys.exit(1)
    
        # Commit and close
        conn.commit()
        conn.close()

def fetch(host, samples):
    database = Database(host)
    res = database.fetch(samples=samples)
    print(json.dumps(res, cls=DateTimeEncoder, sort_keys=True, indent=4), flush=True)


if __name__ == '__main__':
    main()
