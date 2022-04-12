#!/usr/bin/python3

from systemmonitor.collector import *


class IPMICollector(AbstractCollector):

    def collect(self, data):
        if check_installed("ipmitool"):
            try:
                sdr_res = cmd("ipmitool -c sdr")
                sensors = {}
                for line in sdr_res.split("\n"):
                    columns = line.split(',')
                    if columns[3] not in ['ns', '0.0']:
                        key = "hardware.ipmi.{0}".format(columns[0])
                        data["{0}.value".format(key)] = Measurement(float(columns[1]), 'raw', unit=columns[2])
                        data["{0}.ok".format(key)] = Measurement(columns[3] == 'ok', 'bool')
            except CommandException as e:
                err("IPMI command failed:", e.error)
