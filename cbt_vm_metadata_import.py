#!/usr/bin/env python3

"""
For a given vm and old/new VDI pairs this script will import the metadata of
a VM pointing to a new set of VDIs. This script should be run when you want
to make a new VM from a backup. The new VDIs containing the backup data should
be created before this script is run.

example: python cbt_vm_metadata_import.py -ip <host address>
-u <host username> -p <host password> -v <vm uuid> -i <metadata output path>
<old vdi uuid> <new vdi uuid> ...
"""


import XenAPI
import shutil
import urllib3
import requests
import argparse
import re
import sys


def import_vm(host, session, import_path, vdis=None):

    if len(vdis) % 2 != 0:
        print("Error: VDIs should be included in new/old uuid pairs")
        sys.exit(1)

    vdi_string = ""
    for x in range(0, len(vdis), 2):
        vdi_string += "&vdi:%s=%s" % (vdis[x], vdis[x + 1])

    task_ref = session.xenapi.task.create("import_vm",
                                          "Task to track vm import")

    url = ('https://%s/import_metadata?session_id=%s&task_id=%s%s'
           % (host, session._session, task_ref, vdi_string))

    with open(import_path, 'r') as filehandle:
        # ToDo: Security - We need to verify the SSL certificate here.
        # Depends on CP-23051.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        with requests.Session() as http_session:
            request = http_session.put(url, filehandle, verify=False)
            request.raise_for_status()

    result = session.xenapi.task.get_result(task_ref)
    match = re.search(r'OpaqueRef:?([^\<>]+)', result)
    vm_ref = match.group(0)
    return vm_ref


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--host-ip', dest='host')
    parser.add_argument('-u', '--username', dest='username')
    parser.add_argument('-p', '--password', dest='password')
    parser.add_argument('-v', '--vm-uuid', dest='vm_uuid')
    parser.add_argument('-i', '--input-path', dest='input_path')
    parser.add_argument('vars', nargs='*')
    args = parser.parse_args()
    session = XenAPI.Session("https://" + args.host, ignore_ssl=True)
    session.login_with_password(args.username, args.password, "0.1",
                                "CBT example")

    try:
        new_vm_ref = import_vm(args.host, session, args.input_path, args.vars)
        print(new_vm_ref)

    finally:
        session.xenapi.session.logout()


if __name__ == "__main__":
    main()
