#!/usr/bin/python3

from systemmonitor.collector import *


btrfs_filesystem_regex = re.compile(r'Label:\s*(\S+)\s+uuid:\s+(\S+)')
btrfs_device_regex = re.compile(r'\s*devid\s+(\S+)\s+size\s+(\S+)\s+used\s+(\S+)\s+path\s+(\S+)')
btrfs_device_missing_regex = re.compile(r'\s*\*\*\*\s*Some devices missing\s*')


class BtrfsCollector(AbstractCollector):

    def collect(self, data):
        if check_installed("btrfs"):
            disk_devices = self.get_disk_devices()
            btrfs_filesystems = self.get_btrfs_devices(disk_devices)
            self.data_btrfs_device_stats(data, btrfs_filesystems)

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

    def data_btrfs_device_stats(self, data, filesystems):
        for filesystem in filesystems:
            for device in filesystems[filesystem]['devices']:
                data["btrfs.filesystem.{0}.devices_missing".format(filesystem)] = Measurement(filesystems[filesystem]['devices_missing'], 'bool')
                try:
                    out = cmd("sudo btrfs device stats {}".format(device))
                    for line in out.split("\n"):
                        row = line.split()
                        measure = row[0].split('.')[1]
                        count = int(row[1])
                        key = "btrfs.filesystem.{0}.device.{1}.stats.{2}".format(filesystem, device, measure)
                        data[key] = Measurement(float(count), 'raw')
                except CommandException as e:
                    err("btrfs command failed:", e.error)
