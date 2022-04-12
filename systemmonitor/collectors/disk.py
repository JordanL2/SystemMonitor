#!/usr/bin/python3

from systemmonitor.collector import *


class DiskCollector(AbstractCollector):

    def collect(self, data):
        # Disk Usage
        disk_devices = self.get_disk_devices()
        for device in disk_devices:
            self.data_disk_usage(data, device)

        # Disk SMART Info
        for device in disk_devices:
            self.data_disk_smart(data, device['name'])

    def get_disk_devices(self):
        result = cmd('lsblk -pnJb -o NAME,FSAVAIL,FSUSE%')
        devices = json.loads(result)
        return devices['blockdevices']

    def data_disk_usage(self, data, device):
        key = "hardware.disk.{0}".format(device['name'])
        if device['fsuse%'] is not None:
            data["{0}.usage".format(key)] = Measurement(float(device['fsuse%'][0:-1]), '%')
        if device['fsavail'] is not None:
            data["{0}.available".format(key)] = Measurement(int(device['fsavail']), 'bytes')
        if 'children' in device:
            for child in device['children']:
                child_key = "{0}.partition.{1}".format(key, child['name'])
                if child['fsuse%'] is not None:
                    data["{0}.usage".format(child_key)] = Measurement(float(child['fsuse%'][0:-1]), '%')
                if child['fsavail'] is not None:
                    data["{0}.available".format(child_key)] = Measurement(int(child['fsavail']), 'bytes')

    def data_disk_smart(self, data, device_name):
        if check_installed("smartctl"):
            try:
                key = "hardware.disk.{0}.SMART".format(device_name)

                status = json.loads(cmd("sudo smartctl -Hj {0}".format(device_name)))
                data["{0}.passed".format(key)] = Measurement(status['smart_status']['passed'], 'bool')

                details = json.loads(cmd("sudo smartctl -Aj {0}".format(device_name)))
                if details['device']['type'] == 'sat':
                    for attribute in details['ata_smart_attributes']['table']:
                        data["{0}.attributes.{1}".format(key, attribute['name'])] = Measurement(float(attribute['raw']['value']), 'raw')
                elif details['device']['type'] == 'nvme':
                    for attribute, value in details['nvme_smart_health_information_log'].items():
                        if type(value) == list:
                            for i, v in enumerate(value):
                                data["{0}.attributes.{1}.{2}".format(key, attribute, i)] = Measurement(float(v), 'raw')
                        else:
                            data["{0}.attributes.{1}".format(key, attribute)] = Measurement(float(value), 'raw')
            except CommandException as e:
                err("SMART command failed:", e.error)
