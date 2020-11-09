# SystemMonitor

## TYPES

* % = numerical percentage (float)
* %s = numerical percentage delta (float) * seconds
* raw = raw number (float)
* bytes = data size in bytes (int)
* string = string
* date = datetime
* bool = boolean ('True' or 'False')


## MEASUREMENTS

### Hardware
* hardware.memory.{FIELD} => %
* hardware.cpu.utilisation.{NUM}.{TYPE} => %s
* hardware.disk.{DEVICE}.usage => %
* hardware.disk.{DEVICE}.available => bytes
* hardware.disk.{DEVICE}.partition.{PARTITION}.usage => %
* hardware.disk.{DEVICE}.partition.{PARTITION}.available => bytes
* hardware.disk.{DEVICE}.SMART.passed => bool
* hardware.disk.{DEVICE}.SMART.attributes.{ATTRIBUTE_NAME} => raw
* hardware.ipmi.{FIELD}.value => raw (unit)
* hardware.ipmi.{FIELD}.ok => bool

### Shares
* share.{SHARE}.lastsync => date
