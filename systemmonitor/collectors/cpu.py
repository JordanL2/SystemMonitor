#!/usr/bin/python3

from systemmonitor.collector import *


class CPUCollector(AbstractCollector):

    def collect(self, data):
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
                        data[measurement_name] = Measurement(float(fields[i]) / clock_ticks_per_second * 100, '%s')
            # Divide the 'all' stats by the number of CPUs
            for i in range(0, len(fields)):
                measurement_name = "hardware.cpu.utilisation.all.{0}".format(field_names[i])
                data[measurement_name] = Measurement(data[measurement_name].value / cpu_count, data[measurement_name].type)
