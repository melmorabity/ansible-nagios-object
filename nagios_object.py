#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright © 2017-2018 Mohamed El Morabity
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <http://www.gnu.org/licenses/>.


import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import BOOLEANS


DOCUMENTATION = '''
---
module: nagios_object
author: Mohamed El Morabity
short_description: Manage object definitions on Nagios.
description:
  - Manage object definitions on Nagios, using the pynag library.
  - This module only works on Python 2, since the pynag library isn't available yet for Python 3.
options:
  path:
    description:
      - Path to the file where Nagios object will be written.
      - This only applies to new objects. If the object already exists in Nagios, modifications will be done on the configuration file which actually defines the object.
      - If no path is specified, new objects will be written in the Nagios configuration directory, in pynag/<object type>/<object description>.cfg.
      - Be sure to set up Nagios to allow the specified path to be loaded (using the cfg_file/cfg_dir attributes in nagios.cfg)!
    type: path
    required: False
    aliases:
      - dest
      - destfile
      - name
  type:
    description: Nagios object type.
    type: string
    required: True
    choices:
      - host
      - hostgroup
      - service
      - servicegroup
      - contact
      - contactgroup
      - timeperiod
      - command
      - servicedependency
      - serviceescalation
      - hostdependency
      - hostescalation
  parameters:
    description:
      - Nagios object attributes.
      - Attribute values must be integers, strings or null.
      - To remove an attribute from an existing Nagios object, its value can be set to null.
    type: dict
    required: False
  state:
    description:
      - Assert the state of the object.
      - If absent, the object will be removed, as well as references to this one (for example, if you delete a host, remove its name from all hostgroup members entries).
    type: string
    choices:
      - present
      - absent
    required: False
    default: present
  update:
    description:
      - Use to control if resource parameters must be updated if the resource exists.
      - If enabled, the resource will be updated with specified parameters.
    type: boolean
    required: False
    default: True
  validate:
    description:
      - Validate the Nagios configuration, after changes, by running "nagios -v" on the Nagios configuration file.
      - If validation fails, changes are rolled back.
    type: boolean
    required: False
    default: False
  nagios_cfg:
    description:
      - Path to the main Nagios configuration file nagios.cfg.
      - If no path is specified, such a path will be detected automatically.
    type: path
    required: False
  nagios_bin:
    description:
      - Path to the Nagios executable file, called if validatation is enabled.
      - If no path is specified, such a path will be detected automatically.
    type: path
    required: False
  backup:
    description:
      - Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    required: False
    default: False
  follow:
    description:
      - This flag indicates that filesystem links, if they exist, should be followed.
    type: bool
    required: False
    default: False
  others:
    description:
      - All arguments accepted by the file module also work here.
    required: False
'''

EXAMPLES = '''
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
'''


try:
    from pynag import Control, Model
    from pynag.Model import ObjectDefinition

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def is_exe(path):
    """Check whether a given path corresponds to an executable file."""

    return os.path.isfile(path) and os.access(path, os.X_OK)


def get_nagios_bin(program='nagios'):
    """Try to find Nagios executable by searching PATH environment variable."""

    for path in os.environ['PATH'].split(os.pathsep):
        nagios_bin = os.path.join(path, program)
        if is_exe(nagios_bin):
            return nagios_bin

    return None


def get_nagios_object(module):
    """Get a Nagios object from Nagios configuration files, given its attributes."""

    nagios_object_type = module.params.get('type')
    parameters = module.params.get('parameters')

    if parameters.get('register', 1) == 0:
        # Template object
        nagios_object_key = 'name'
        nagios_object_id = parameters.get(nagios_object_key, None)
        if nagios_object_id is None:
            module.fail_json(
                msg='{} parameter must be defined for {} object template'.format(nagios_object_key,
                                                                                 nagios_object_type)
            )
        nagios_object_ids = {nagios_object_key: nagios_object_id}
    else:
        if nagios_object_type == 'service':
            service_description = parameters.get('service_description')
            if service_description is None:
                module.fail_json(
                    msg='service_description attribute must be defined for service objects'
                )
            nagios_object_ids = {
                'service_description': service_description,
                'host_name': parameters.get('host_name'),
                'hostgroup_name': parameters.get('hostgroup_name')
            }
        elif nagios_object_type == 'servicedependency':
            nagios_object_ids = {
                'host_name': parameters.get('host_name'),
                'dependent_host_name': parameters.get('dependent_host_name'),
                'hostgroup_name': parameters.get('hostgroup_name'),
                'dependent_hostgroup_name': parameters.get('dependent_hostgroup_name'),
                'service_description': parameters.get('service_description'),
                'dependent_service_description': parameters.get('dependent_service_description'),
                'servicegroup_name': parameters.get('servicegroup_name'),
                'dependent_servicegroup_name': parameters.get('dependent_servicegroup_name')
            }
        elif nagios_object_type == 'hostdependency':
            nagios_object_ids = {
                'host_name': parameters.get('host_name'),
                'hostgroup_name': parameters.get('hostgroup_name'),
                'dependent_host_name': parameters.get('dependent_host_name'),
                'dependent_hostgroup_name': parameters.get('dependent_hostgroup_name'),
            }
        else:
            nagios_object_key = Model.config.object_type_keys[nagios_object_type]
            nagios_object_id = parameters.get(nagios_object_key, None)
            if nagios_object_id is None:
                module.fail_json(
                    msg='{} parameter must be defined for {} objects'.format(nagios_object_key,
                                                                             nagios_object_type)
                )
            nagios_object_ids = {nagios_object_key: nagios_object_id}

    try:
        nagios_objects = ObjectDefinition.objects.filter(object_type=nagios_object_type,
                                                         **nagios_object_ids)
    except Exception as ex:
        module.fail_json(msg='Failed to check Nagios object availability: {}'.format(ex))

    if not nagios_objects:
        return None

    if len(nagios_objects) > 1:
        module.fail_json(msg='More than one Nagios object found matching parameter IDs')

    return nagios_objects[0]


def create_nagios_object(module):
    """Create or update a Nagios object."""

    nagios_object_type = module.params.get('type')
    parameters = module.params.get('parameters')
    update = module.params.get('update')
    path = module.params.get('path')
    backup = module.params.get('backup')
    validate = module.params.get('validate')

    nagios_object = get_nagios_object(module)
    backup_file = ''

    if nagios_object is None:
        # Nagios object will be created
        before = ''
        changed = True
        nagios_object = Model.string_to_class[nagios_object_type](filename=path,
                                                                  **parameters)
        nagios_object_file = nagios_object.get_filename()
    else:
        before = str(nagios_object)
        nagios_object_file = nagios_object.get_filename()
        if update:
            for key, value in parameters.iteritems():
                nagios_object.set_attribute(key, value)

        changed = nagios_object.is_dirty()

    if changed:
        # Back up file Nagios object file, in case of rollback after failing validation
        if backup or validate:
            # backup_local() returns empty string is file to backup doesn't exist
            backup_file = module.backup_local(nagios_object_file)

        try:
            nagios_object.save()
        except Exception as ex:
            module.fail_json(msg='Failed to write Nagios object: {}'.format(ex), ex=vars(ex))
        nagios_object_file = nagios_object.get_filename()
        after = str(nagios_object)
    else:
        after = before

    return (changed, nagios_object_file, nagios_object['meta']['defined_attributes'], before, after,
            backup_file)


def delete_nagios_object(module):
    """Delete a Nagios object."""

    nagios_object = get_nagios_object(module)

    if nagios_object is None:
        return (False, None, None, '', '', None)

    backup = module.params.get('backup')
    validate = module.params.get('validate')

    nagios_object_file = nagios_object.get_filename()
    before = str(nagios_object)
    backup_file = None

    # Back up file Nagios object file, in case of rollback after failing validation
    if backup or validate:
        backup_file = module.backup_local(nagios_object_file)

    nagios_object.delete(recursive=False, cleanup_related_items=True)
    return (True, nagios_object_file, nagios_object['meta']['defined_attributes'], before, '',
            backup_file)


def validate_nagios_configuration(module, backup_file):
    """Validate a Nagios configuration. If it fails, roll back previous changes."""

    path = module.params.get('path')
    backup = module.params.get('backup')
    nagios_bin = module.params.get('nagios_bin')
    nagios_cfg = module.params.get('nagios_cfg')

    nagios_daemon = Control.daemon(nagios_bin=nagios_bin, nagios_cfg=nagios_cfg)

    if nagios_daemon.verify_config():
        if not backup and backup_file is not None:
            # Remove backup file since validation successed
            module.cleanup(backup_file)
        return

    if backup_file == '':
        # Delete newly created Nagios file
        module.cleanup(path)
    else:
        # Restore original Nagios file from backup
        module.atomic_move(backup_file, path)

    # If validation process cannot be run, error messages are displayed on stdout
    message = nagios_daemon.stdout or nagios_daemon.stderr
    module.fail_json(msg='Nagios configuration validation failed: {}'.format(message))


def main():
    """Main execution path."""

    module = AnsibleModule(
        argument_spec={
            'path': {'aliases': ['dest', 'destfile', 'name'], 'type': 'path'},
            'type': {'required': True, 'type': 'str', 'choices': ['host', 'hostgroup', 'service',
                                                                  'servicegroup', 'contact',
                                                                  'contactgroup', 'timeperiod',
                                                                  'command', 'servicedependency',
                                                                  'serviceescalation',
                                                                  'hostdependency',
                                                                  'hostescalation']},
            'parameters': {'required': True, 'type': 'dict'},
            'state': {'type': 'str', 'choices': ['present', 'absent'], 'default': 'present'},
            'update': {'type': 'bool', 'choices': BOOLEANS, 'default': True},
            'validate': {'type': 'bool', 'choices': BOOLEANS, 'default': False},
            'nagios_cfg': {'type': 'path'},
            'nagios_bin': {'type': 'path'},
            'backup': {'type': 'bool', 'choices': BOOLEANS, 'default': False}
        },
        add_file_common_args=True,
        supports_check_mode=True
    )

    if not HAS_LIB:
        module.fail_json(msg='pynag is required for this module')

    nagios_cfg = module.params.get('nagios_cfg')
    if nagios_cfg is None:
        module.params['nagios_cfg'] = Model.config.cfg_file
    if nagios_cfg is not None:
        if not os.path.isfile(nagios_cfg):
            module.fail_json(msg='Nagios configuration file {} does not exist'.format(nagios_cfg))
        Model.cfg_file = nagios_cfg

    if module.params.get('validate'):
        # Validation requires the nagios executable
        nagios_bin = module.params.get('nagios_bin')
        if nagios_bin is None:
            module.params['nagios_bin'] = get_nagios_bin()
            if module.params.get('nagios_bin') is None:
                module.fail_json(msg='Could not find Nagios executable, required by validate')
        else:
            if not is_exe(nagios_bin):
                module.fail_json(
                    msg='Nagios executable {} does not exist or is not executable'.format(
                        nagios_bin
                    )
                )

    # Validate types for each specified Nagios object attribute
    for key, value in module.params.get('parameters').iteritems():
        if value is not None and not isinstance(value, str) and \
           (isinstance(value, bool) or not isinstance(value, int)):
            module.fail_json(msg='{} parameter item must be null, integer or string'.format(key))

    if module.params.get('state') == 'present':
        (changed, path, nagios_object, before, after, backup_file) = create_nagios_object(module)
    else:
        (changed, path, nagios_object, before, after, backup_file) = delete_nagios_object(module)
    # Update path to the real updated Nagios object file
    module.params['path'] = path

    if changed and module.params.get('validate'):
        validate_nagios_configuration(module, backup_file)

    file_args = module.load_file_common_arguments(module.params)
    changed |= module.set_fs_attributes_if_different(file_args, changed)

    results = {'changed': changed, 'path': path, 'nagios_object': nagios_object}
    if module._diff:
        results['diff'] = {'before_header': path, 'before': before, 'after_header': path,
                           'after': after}

    if module.params.get('backup'):
        results['backup_file'] = backup_file
    module.exit_json(**results)


if __name__ == '__main__':
    main()
