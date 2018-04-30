# nagios_object

Manage object definitions on Nagios.

## Synopsis

* Manage object definitions on Nagios, using the pynag library.
* This module only works on Python 2, since the pynag library isn't available yet for Python 3.

## Requirements

The below requirements are needed on the host that executes this module.

* pynag

## Options

| parameter  | required | default | choices                                                                                                                                                                                                                                                 | comments                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| parameters | no       |         |                                                                                                                                                                                                                                                         | Nagios object attributes. Attribute values must be integers, strings or null. To remove an attribute from an existing Nagios object, its value can be set to null.                                                                                                                                                                                                                                                                                                                                              |
| type       | yes      |         | <ul><li>host</li><li>hostgroup</li><li>service</li><li>servicegroup</li><li>contact</li><li>contactgroup</li><li>timeperiod</li><li>command</li><li>servicedependency</li><li>serviceescalation</li><li>hostdependency</li><li>hostescalation</li></ul> | Nagios object type.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| nagios_cfg | no       |         |                                                                                                                                                                                                                                                         | Path to the main Nagios configuration file nagios.cfg. If no path is specified, such a path will be detected automatically.                                                                                                                                                                                                                                                                                                                                                                                     |
| update     | no       | True    |                                                                                                                                                                                                                                                         | Use to control if resource parameters must be updated if the resource exists. If enabled, the resource will be updated with specified parameters.                                                                                                                                                                                                                                                                                                                                                               |
| nagios_bin | no       |         |                                                                                                                                                                                                                                                         | Path to the Nagios executable file, called if validatation is enabled. If no path is specified, such a path will be detected automatically.                                                                                                                                                                                                                                                                                                                                                                     |
| state      | no       | present | <ul><li>present</li><li>absent</li></ul>                                                                                                                                                                                                                | Assert the state of the object. If absent, the object will be removed, as well as references to this one (for example, if you delete a host, remove its name from all hostgroup members entries).                                                                                                                                                                                                                                                                                                               |
| others     | no       |         |                                                                                                                                                                                                                                                         | All arguments accepted by the file module also work here.                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| follow     | no       | False   |                                                                                                                                                                                                                                                         | This flag indicates that filesystem links, if they exist, should be followed.                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| path       | no       |         |                                                                                                                                                                                                                                                         | Path to the file where Nagios object will be written. This only applies to new objects. If the object already exists in Nagios, modifications will be done on the configuration file which actually defines the object. If no path is specified, new objects will be written in the Nagios configuration directory, in pynag/&lt;object type&gt;/&lt;object description&gt;.cfg. Be sure to set up Nagios to allow such configuration paths to be loaded (using the cfg_file/cfg_dir attributes in nagios.cfg)! |
| backup     | no       | False   |                                                                                                                                                                                                                                                         | Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.                                                                                                                                                                                                                                                                                                                                                                         |
| validate   | no       | False   |                                                                                                                                                                                                                                                         | Validate the Nagios configuration, after changes, by running "nagios -v" on the Nagios configuration file.  If validation fails, changes are rolled back.                                                                                                                                                                                                                                                                                                                                                       |

## Examples

```
# Create a new host
- local_action:
    module: nagios_object
    type: host
    parameters:
      host_name: host1
      alias: Host 1
      use: generic-host

# Add service to the previous host
- local_action:
    module: nagios_object
    type: service
    parameters:
      host: host1
      service_description: Ping
      check_command: check_ping!100.0,20%!500.0,60%
      use: generic-service
```
