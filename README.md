# SystemMonitor

## INSTALLATION

### Requirements

* python >= 3.5
* mariadb-clients
* yaml.h (libyaml-devel on OpenSUSE)
* python modules:
	* mariadb
	* pyyaml

### Install

```
sudo ./install
```

Make sure you set up the config file before using.

## USAGE

### Configuration

There is an example config included: `systemmonitor.yml`.

Configuration is looked for in these places, in order, until one is found:

* \~/.config/systemmonitor.yml
* /usr/local/etc/systemmonitor.yml
* /etc/systemmonitor.yml

Copy the example config file to one of those places. Warning: The systemmonitor (logging) service runs as root by default.

### Set up to monitor local host

1. Set up database:
	1. Install Maria DB server
	2. Connect to it as root
	3. Run commands in systemmonitor.sql (change the default user config/passwords if wanted)
2. ```sudo systemctl enable --now systemmonitor.timer```

### Set up to read monitoring info from another host

For this example the remote host is called `henry`.

Put this config at `/usr/local/etc/systemmonitor.yml`:

```
henry:
  db:
    read:
      user: monitor_select
      pass: qwerty
    host: henry
    schema: monitor
```

You can now read the remote host's monitoring info using the command line tool, or the Python library.

### Using command line tool

```
systemmonitor-read <HOSTNAME> [<SAMPLES>]
```

Example:
```
systemmonitor-read henry 2
```

### Example Python script using library


Script:

```
#!/usr/bin/python3

from systemmonitor.monitorapi import MonitorApi


m = MonitorApi('henry')
data = m.get(samples=2)

print(data)
```

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
