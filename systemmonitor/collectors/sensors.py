#!/usr/bin/python3

from systemmonitor.collector import *


sensor_regex = re.compile(r'(\D+)(\d*)(?:_(.+))?')


class SensorsCollector(AbstractCollector):

    def collect(self, data):
        if check_installed("sensors"):
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
                            data[key] = Measurement(float(value), 'raw')
            except CommandException as e:
                err("Sensors command failed:", e.error)
