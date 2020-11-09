CREATE DATABASE monitor;

CREATE TABLE monitor.measurements (
	taken       DATETIME     NOT NULL,
	measurement VARCHAR(100) NOT NULL,
	value_type  VARCHAR(10)  NOT NULL,
	value       VARCHAR(100) NOT NULL,
	unit        VARCHAR(20),
	INDEX (taken),
	INDEX (measurement)
);

# User for adding data to monitoring
CREATE USER monitor_insert@'localhost' IDENTIFIED BY 'qwerty' PASSWORD EXPIRE NEVER;
GRANT INSERT ON monitor.measurements TO 'monitor_insert'@'localhost';

# User for reading data from monitoring
CREATE USER monitor_select IDENTIFIED BY 'qwerty' PASSWORD EXPIRE NEVER;
GRANT SELECT ON monitor.measurements TO 'monitor_select';
