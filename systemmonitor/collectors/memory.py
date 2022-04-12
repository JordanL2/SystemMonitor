#!/usr/bin/python3

from systemmonitor.collector import *


class MemoryCollector(AbstractCollector):

    def collect(self, data):
        result = cmd('free -wb | head -n2 | tail -n+2')
        line_regex = re.compile('^Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
        line_match = line_regex.match(result)
        if line_match:
            field_names = ('total', 'used', 'free', 'shared', 'buffers', 'cache', 'available')
            total = int(line_match.group(1))
            for i in range(1, len(field_names)):
                data["hardware.memory.{0}".format(field_names[i])] = Measurement(int(line_match.group(i + 1)) / total * 100, '%')
