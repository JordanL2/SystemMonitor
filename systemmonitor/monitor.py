#!/usr/bin/python3

from datetime import *
import json
import mariadb
import re
import subprocess
import yaml


def main():
    # Load config
    config_file = '/usr/local/etc/systemmonitor.yml'
    with open(config_file, 'r') as fh:
        config = yaml.load(fh)
    local_config = config['localhost']

    db_user = local_config['db']['push']['user']
    db_pass = local_config['db']['push']['pass']
    db_host = local_config['db']['host']
    db_schema = local_config['db']['schema']
    
    shares = []
    if 'shares' in local_config:
        shares = local_config['shares']

    # Get timestamp
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(now)


    #
    # GATHER DATA
    #
    
    data = dict()


    ### HARDWARE ###

    # Memory
    data_memory_usage(data)

    # CPU Utilisation
    data_cpu_utilisation(data)

    # Disk Usage
    disk_devices = get_disk_devices()
    print("Found disk devices:", disk_devices)
    for device in disk_devices:
        data_disk_usage(data, device)

    # Disk SMART Info
    for device in disk_devices:
        data_disk_smart(data, device['name'])

    # IPMI Info
    data_ipmi(data)


    ### CUSTOM ###

    if 'custom' in local_config:
        for key, custom_config in local_config['custom'].items():
            params = custom_config['input']
            if custom_config['method'] == 'file_date_modified':
                data_file_date_modified(data, key, params[0])

    #
    # INSERT DATA INTO DB
    #

    # Get connection
    try:
        conn = mariadb.connect(
            user = db_user,
            password = db_pass,
            host = db_host,
            database = db_schema
        )
    except mariadb.Error as e:
        print(f"Error connecting: {e}")
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
            print(f"Error inserting data: {e}")
            conn.close()
            sys.exit(1)

    # Commit and close
    conn.commit()
    conn.close()


### DATA FETCHING ###

def data_memory_usage(data):
    result = cmd('free -wb | head -n2 | tail -n+2')
    line_regex = re.compile('^Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
    line_match = line_regex.match(result)
    if line_match:
        field_names = ('total', 'used', 'free', 'shared', 'buffers', 'cache', 'available')
        total = int(line_match.group(1))
        for i in range(1, len(field_names)):
            data["hardware.memory.{0}".format(field_names[i])] = (int(line_match.group(i + 1)) / total * 100, '%')

def data_cpu_utilisation(data):
    clock_ticks_per_second = float(cmd('getconf CLK_TCK'))
    with open('/proc/stat') as f:
        raw = f.read()
        line_regex = re.compile('^cpu(\d*)\s+(.+)')
        for line in raw.split("\n"):
            line_match = line_regex.match(line)
            if line_match:
                cpu = line_match.group(1)
                if cpu == '':
                    cpu = 'all'
                fields = line_match.group(2).split(' ')
                field_names = ('user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice')
                for i in range(0, len(fields)):
                    measurement_name = "hardware.cpu.utilisation.{0}.{1}".format(cpu, field_names[i])
                    data[measurement_name] = (float(fields[i]) / clock_ticks_per_second * 100, '%s')

def data_disk_usage(data, device):
    key = "hardware.disk.{0}".format(device['name'])
    if device['fsuse%'] is not None:
        data["{0}.usage".format(key)] = (float(device['fsuse%'][0:-1]), '%')
    if device['fsavail'] is not None:
        data["{0}.available".format(key)] = (int(device['fsavail']), 'bytes')
    if 'children' in device:
        for child in device['children']:
            child_key = "{0}.partition.{1}".format(key, child['name'])
            if child['fsuse%'] is not None:
                data["{0}.usage".format(child_key)] = (float(child['fsuse%'][0:-1]), '%')
            if child['fsavail'] is not None:
                data["{0}.available".format(child_key)] = (int(child['fsavail']), 'bytes')

def data_disk_smart(data, device_name):
    key = "hardware.disk.{0}.SMART".format(device_name)

    status = json.loads(cmd("smartctl -Hj {0}".format(device_name)))
    data["{0}.passed".format(key)] = (status['smart_status']['passed'], 'bool')

    details = json.loads(cmd("smartctl -Aj {0}".format(device_name)))
    if details['device']['type'] == 'sat':
        for attribute in details['ata_smart_attributes']['table']:
            data["{0}.attributes.{1}".format(key, attribute['name'])] = (float(attribute['raw']['value']), 'raw')
    elif details['device']['type'] == 'nvme':
        for attribute, value in details['nvme_smart_health_information_log'].items():
            data["{0}.attributes.{1}".format(key, attribute)] = (float(value), 'raw')

def data_ipmi(data):
    sdr_res = cmd("ipmitool -c sdr")
    sensors = {}
    for line in sdr_res.split("\n"):
        columns = line.split(',')
        if columns[3] not in ['ns', '0.0']:
            key = "hardware.ipmi.{0}".format(columns[0])
            data["{0}.value".format(key)] = (float(columns[1]), 'raw', columns[2])
            data["{0}.ok".format(key)] = (columns[3] == 'ok', 'bool')


### Custom methods ###

def data_file_date_modified(data, key, filename):
    result = cmd("ls -l --time-style=+'%Y-%m-%d %H:%M:%S' {0} | cut -d' ' -f 6,7".format(filename))
    data[key] = (result, 'date')


### OTHER ###

def cmd(command):
    print("--- CMD:", command)
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8').rstrip("\n")
    stderr = result.stderr.decode('utf-8').rstrip("\n")
    print("  | OUT:", stdout)
    print("  | ERR:", stderr)
    if result.returncode != 0:
        raise Exception("Command returned code {}".format(result.returncode))
    return stdout

def get_disk_devices():
    result = cmd('lsblk -pnJb -o NAME,FSAVAIL,FSUSE%')
    devices = json.loads(result)
    return devices['blockdevices']


### ENTRY POINT ###

if __name__ == '__main__':
    main()
