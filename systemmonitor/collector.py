#!/usr/bin/python3

from systemmonitor.common import *

from datetime import *
import re


sensor_regex = re.compile(r'(\D+)(\d*)_(.+)')
btrfs_filesystem_regex = re.compile(r'Label:\s*(\S+)\s+uuid:\s+(\S+)')
btrfs_device_regex = re.compile(r'\s*devid\s+(\S+)\s+size\s+(\S+)\s+used\s+(\S+)\s+path\s+(\S+)')
btrfs_device_missing_regex = re.compile(r'\s*\*\*\*\s*Some devices missing\s*')


class Collector():

    def __init__(self):
        # Load config
        local_config = get_config('localhost')
        self.local_config = local_config
    
    def collect(self, structured_data=True):
        data = dict()
    
    
        ### HARDWARE ###
    
        # Memory
        self.data_memory_usage(data)
    
        # CPU Utilisation
        self.data_cpu_utilisation(data)
    
        # Disk Usage
        disk_devices = self.get_disk_devices()
        for device in disk_devices:
            self.data_disk_usage(data, device)
    
        # Disk SMART Info
        for device in disk_devices:
            self.data_disk_smart(data, device['name'])
        
        # Btrfs device stats
        btrfs_filesystems = self.get_btrfs_devices(disk_devices)
        self.data_btrfs_device_stats(data, btrfs_filesystems)
    
        # IPMI Info
        self.data_ipmi(data)
    
        # Sensor info
        self.data_sensors(data)
    
    
        ### CUSTOM ###
    
        if self.local_config is not None and 'custom' in self.local_config:
            for key, custom_config in self.local_config['custom'].items():
                params = custom_config['input']
                if custom_config['method'] == 'file_date_modified':
                    self.data_file_date_modified(data, key, *params)
        
        
        # Return data, structered hierarchically if required
        if structured_data:
            return structure_data(data)
        return data
    
    
    ### DATA FETCHING ###
    
    def data_memory_usage(self, data):
        result = cmd('free -wb | head -n2 | tail -n+2')
        line_regex = re.compile('^Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
        line_match = line_regex.match(result)
        if line_match:
            field_names = ('total', 'used', 'free', 'shared', 'buffers', 'cache', 'available')
            total = int(line_match.group(1))
            for i in range(1, len(field_names)):
                data["hardware.memory.{0}".format(field_names[i])] = {
                    'value': int(line_match.group(i + 1)) / total * 100,
                    'type': '%',
                }
    
    def data_cpu_utilisation(self, data):
        clock_ticks_per_second = float(cmd('getconf CLK_TCK'))
        field_names = ('user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice')
        with open('/proc/stat') as f:
            raw = f.read()
            line_regex = re.compile('^cpu(\d*)\s+(.+)')
            cpu_count = 0
            for line in raw.split("\n"):
                line_match = line_regex.match(line)
                if line_match:
                    cpu = line_match.group(1)
                    if cpu == '':
                        cpu = 'all'
                    else:
                        cpu_count += 1
                    fields = line_match.group(2).split(' ')
                    for i in range(0, len(fields)):
                        measurement_name = "hardware.cpu.utilisation.{0}.{1}".format(cpu, field_names[i])
                        data[measurement_name] = {
                            'value': float(fields[i]) / clock_ticks_per_second * 100,
                            'type': '%s',
                        }
            # Divide the 'all' stats by the number of CPUs
            for i in range(0, len(fields)):
                measurement_name = "hardware.cpu.utilisation.all.{0}".format(field_names[i])
                data[measurement_name] = {
                    'value': data[measurement_name]['value'] / cpu_count,
                    'type': data[measurement_name]['type'],
                }
    
    def data_disk_usage(self, data, device):
        key = "hardware.disk.{0}".format(device['name'])
        if device['fsuse%'] is not None:
            data["{0}.usage".format(key)] = {
                'value': float(device['fsuse%'][0:-1]),
                'type': '%',
            }
        if device['fsavail'] is not None:
            data["{0}.available".format(key)] = {
                'value': int(device['fsavail']),
                'type': 'bytes',
            }
        if 'children' in device:
            for child in device['children']:
                child_key = "{0}.partition.{1}".format(key, child['name'])
                if child['fsuse%'] is not None:
                    data["{0}.usage".format(child_key)] = {
                        'value': float(child['fsuse%'][0:-1]),
                        'type': '%',
                    }
                if child['fsavail'] is not None:
                    data["{0}.available".format(child_key)] = {
                        'value': int(child['fsavail']),
                        'type': 'bytes',
                    }
    
    def data_disk_smart(self, data, device_name):
        try:
            key = "hardware.disk.{0}.SMART".format(device_name)
    
            status = json.loads(cmd("sudo smartctl -Hj {0}".format(device_name)))
            data["{0}.passed".format(key)] = {
                'value': status['smart_status']['passed'],
                'type': 'bool',
            }
    
            details = json.loads(cmd("sudo smartctl -Aj {0}".format(device_name)))
            if details['device']['type'] == 'sat':
                for attribute in details['ata_smart_attributes']['table']:
                    data["{0}.attributes.{1}".format(key, attribute['name'])] = {
                        'value': float(attribute['raw']['value']),
                        'type': 'raw',
                    }
            elif details['device']['type'] == 'nvme':
                for attribute, value in details['nvme_smart_health_information_log'].items():
                    if type(value) == list:
                        for i, v in enumerate(value):
                            data["{0}.attributes.{1}.{2}".format(key, attribute, i)] = {
                                'value': float(v),
                                'type': 'raw',
                            }
                    else:
                        data["{0}.attributes.{1}".format(key, attribute)] = {
                            'value': float(value),
                            'type': 'raw',
                        }
        except CommandException as e:
            err("SMART command failed:", e.error)
    
    def data_btrfs_device_stats(self, data, filesystems):
        for filesystem in filesystems:
            for device in filesystems[filesystem]['devices']:
                data["btrfs.filesystem.{0}.devices_missing".format(filesystem)] = {
                    'value': filesystems[filesystem]['devices_missing'],
                    'type': 'bool',
                }
                try:
                    out = cmd("sudo btrfs device stats {}".format(device))
                    for line in out.split("\n"):
                        row = line.split()
                        measure = row[0].split('.')[1]
                        count = int(row[1])
                        key = "btrfs.filesystem.{0}.device.{1}.stats.{2}".format(filesystem, device, measure)
                        data[key] = {
                            'value': float(count),
                            'type': 'raw',
                        }
                except CommandException as e:
                    err("btrfs command failed:", e.error)
    
    def data_ipmi(self, data):
        try:
            sdr_res = cmd("ipmitool -c sdr")
            sensors = {}
            for line in sdr_res.split("\n"):
                columns = line.split(',')
                if columns[3] not in ['ns', '0.0']:
                    key = "hardware.ipmi.{0}".format(columns[0])
                    data["{0}.value".format(key)] = {
                        'value': float(columns[1]),
                        'type': 'raw',
                        'unit': columns[2],
                    }
                    data["{0}.ok".format(key)] = {
                        'value': columns[3] == 'ok',
                        'type': 'bool',
                    }
        except CommandException as e:
            err("IPMI command failed:", e.error)
    
    def data_sensors(self, data):
        try:
            boundaries = ['min', 'input', 'max', 'crit']
            sensors = json.loads(cmd("sensors -j"))
            sensor_data = {}
            for module in sensors:
                sensor_data[module] = {}
                for sensor in sensors[module]:
                    if sensor == 'Adapter':
                        continue
                    sensor_data[module][sensor] = {}
                    for reading_k, reading_v in sensors[module][sensor].items():
                        reading_match = sensor_regex.match(reading_k)
                        if reading_match:
                            reading_type = reading_match.group(1)
                            reading_type_num = reading_match.group(2)
                            reading_boundary = reading_match.group(3)
                            
                            if 'type' not in sensor_data[module][sensor]:
                                sensor_data[module][sensor]['type'] = reading_type
                            else:
                                if reading_type != sensor_data[module][sensor]['type']:
                                    raise Exception("Multiple reading types in {}/{}".format(module, sensor))
                            
                            if reading_boundary in boundaries:
                                sensor_data[module][sensor][reading_boundary] = reading_v
                        else:
                            raise Exception("Could not parse label '{}'".format(reading_k))
            for module in sensor_data:
                for sensor in sensor_data[module]:
                    sensor_type = sensor_data[module][sensor]['type']
                    for reading_boundary in sensor_data[module][sensor]:
                        if reading_boundary == 'type':
                            continue
                        key = "hardware.sensors.{0}.{1}_{2}.{3}".format(module, sensor, sensor_type, reading_boundary)
                        value = sensor_data[module][sensor][reading_boundary]
                        data[key] = {
                            'value': float(value),
                            'type': 'raw',
                        }
        except CommandException as e:
            err("Sensors command failed:", e.error)
        
    
    ### Custom methods ###
    
    def data_file_date_modified(self, data, key, filename):
        result = cmd("ls -l --time-style=+'%Y-%m-%d %H:%M:%S' {0} | cut -d' ' -f 6,7".format(filename))
        dt = datetime.strptime(result, datetime_format)
        data[key] = {
            'value': dt,
            'type': 'date',
        }
    
    
    ### OTHER ###
    
    def get_disk_devices(self):
        result = cmd('lsblk -pnJb -o NAME,FSAVAIL,FSUSE%')
        devices = json.loads(result)
        return devices['blockdevices']
    
    def get_btrfs_devices(self, devices):
        try:
            filesystems = {}
            filesystem = None
            result = cmd('sudo btrfs filesystem show')
            for line in result.split("\n"):
                regex_match = btrfs_filesystem_regex.match(line)
                if regex_match:
                    filesystem = regex_match.group(2)
                    filesystems[filesystem] = {
                        'devices_missing': False,
                        'devices': [],
                    }
                    continue
                regex_match = btrfs_device_regex.match(line)
                if regex_match:
                    device = regex_match.group(4)
                    filesystems[filesystem]['devices'].append(device)
                    continue
                regex_match = btrfs_device_missing_regex.match(line)
                if regex_match:
                    filesystems[filesystem]['devices_missing'] = True
                    continue
            return filesystems
        except CommandException as e:
            err("btrfs command failed:", e.error)
            return []
