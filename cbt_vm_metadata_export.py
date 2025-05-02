#!/usr/bin/env python3

"""
For a given vm this script will export the metadata not including the vm
snapshot data.

example: python cbt_vm_metadata_export.py -ip <host address> -u <host username>
-p <host password> -v <vm uuid> -o <metadata output path>
"""


import XenAPI
import shutil
import urllib3
import requests
import argparse
import re
import sys


def export_vm(host, session_id, vm_uuid, export_path):
    # export_snapshots option determines whether vm snapshot data is included
    url = ("https://%s/export_metadata?session_id=%s&uuid=%s"
           "&export_snapshots=false"
           % (host, session_id, vm_uuid))

    with requests.Session() as session:
        # ToDo: Security - We need to verify the SSL certificate here.
        # Depends on CP-23051.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        request = session.get(url, verify=False, stream=True)
        with open(export_path, 'wb') as filehandle:
            shutil.copyfileobj(request.raw, filehandle)
        request.raise_for_status()

    print("Metadata saved to: %s" % export_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--host-ip', dest='host')
    parser.add_argument('-u', '--username', dest='username')
    parser.add_argument('-p', '--password', dest='password')
    parser.add_argument('-v', '--vm-uuid', dest='vm_uuid')
    parser.add_argument('-o', '--output-path', dest='output_path')
    args = parser.parse_args()
    session = XenAPI.Session("https://" + args.host, ignore_ssl=True)
    session.login_with_password(args.username, args.password, "0.1",
                                "CBT example")

    try:
        export_vm(args.host, session._session, args.vm_uuid, args.output_path)

    finally:
        session.xenapi.session.logout()


if __name__ == "__main__":
    main()
