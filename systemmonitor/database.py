#!/usr/bin/python3

from systemmonitor.common import *

from datetime import *
import sys


class Database():

    def __init__(self, host):
        # Load config
        host_config = get_config(host)
        
        if 'db' not in host_config:
            raise Exception("No database config found")
        
        self.db_host = host_config['db']['host']
        self.db_schema = host_config['db']['schema']
        self.db_read = False
        self.db_push = False

        if 'read' in host_config['db']:
            self.db_read = True
            self.db_read_user = host_config['db']['read']['user']
            self.db_read_pass = host_config['db']['read']['pass']

        if 'push' in host_config['db']:
            self.db_push = True
            self.db_push_user = host_config['db']['push']['user']
            self.db_push_pass = host_config['db']['push']['pass']

    def fetch(self, samples=None, structured_data=True):
        self.connect_read()
        cur = self.read_connection.cursor()

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
        raw = {}

        for (taken, measurement, value_type, value, unit) in cur:
            
            add_data = True

            if value_type in ('%', 'raw'):
                value = float(value)

            elif value_type == '%s':
                original_value = float(value)
                if measurement in raw:
                    previous_time = sorted(list(raw[measurement].keys()))[-1]
                    delta_seconds = (taken - previous_time).total_seconds()
                    value = (float(value) - raw[measurement][previous_time]) / delta_seconds
                else:
                    add_data = False
                    raw[measurement] = {}
                raw[measurement][taken] = original_value

            elif value_type in ('bytes'):
                value = int(value)

            elif value_type == 'bool':
                value = (value == 'True')

            elif value_type == 'date':
                if value == '':
                    value = None
                else:
                    value = datetime.strptime(value, datetime_format)

            elif value_type == 'string':
                value = value

            else:
                raise Exception("Invalid type: {}".format(value_type))

            if add_data:
                if measurement not in data:
                    data[measurement] = {
                        'value': value,
                        'type': value_type,
                        'values': {
                            taken: value
                        },
                        'latest': taken,
                    } 
                    if unit is not None:
                        data[measurement]['unit'] = unit
                else:
                    data[measurement]['value'] = value
                    data[measurement]['latest'] = taken
                    data[measurement]['values'][taken] = value
        
        self.disconnect_read()

        if structured_data:
            return structure_data(data);
        return data
    
    def push(self, data, now):
        self.connect_push()
        cur = self.push_connection.cursor()

        for key, value_data in data.items():
            unit = None
            if 'unit' in value_data:
                unit = value_data['unit']
            try:
                cur.execute("INSERT INTO measurements (taken, measurement, value_type, value, unit) VALUES (?, ?, ?, ?, ?)", (now, key, value_data['type'], str(value_data['value']), unit))
            except mariadb.Error as e:
                self.push_connection.close()
                raise e
        
        self.push_connection.commit()
        self.disconnect_push()

    def connect_read(self):
        if not self.db_read:
            raise Exception("Read DB config not provided")
        try:
            conn = mariadb.connect(
                user = self.db_read_user,
                password = self.db_read_pass,
                host = self.db_host,
                database = self.db_schema
            )
        except mariadb.Error as e:
            raise e
        self.read_connection = conn

    def disconnect_read(self):
        self.read_connection.close()

    def connect_push(self):
        if not self.db_push:
            raise Exception("Push DB config not provided")
        try:
            conn = mariadb.connect(
                user = self.db_push_user,
                password = self.db_push_pass,
                host = self.db_host,
                database = self.db_schema
            )
            conn.autocommit = False
        except mariadb.Error as e:
            raise e
        self.push_connection = conn

    def disconnect_push(self):
        self.push_connection.close()
