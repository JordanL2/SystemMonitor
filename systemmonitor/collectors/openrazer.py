#!/usr/bin/python3

from systemmonitor.collector import *


class OpenRazerCollector(AbstractCollector):

    def collect(self, data):
        try:
            import openrazer.client

            devices = openrazer.client.DeviceManager().devices

            for device in devices:
                if device.has("battery"):
                    device_name = device.name.replace('.', '_')
                    key = "hardware.peripherals.{}.{}.battery".format(device._type, device_name)
                    data[key] = Measurement(float(device.battery_level), '%')
        except ImportError:
            pass
