# SystemMonitor

## INSTALLATION

### Requirements

* python >= 3.5
* mariadb-clients
* python modules:
	* mariadb
	* pyyaml

### Install

```
sudo ./install
sudo cp ./systemmonitor.yml /usr/local/etc/
```

### Set up to monitor local host

1. Set up database:
	1. Install Maria DB server
	2. Connect to it as root
	3. Run commands in systemmonitor.sql (change the default user config/passwords if wanted)
2. ```systemctl enable --now systemmonitor.timer```

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

### Custom Methods
* file_date_modified(filename) => date
