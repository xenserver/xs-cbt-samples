#!/usr/bin/env python

"""
For a given vdi and import file this script will import a VDI on to a XS host.
This script needs to be run whenever you want to restore a VDI to a previous
version.

example: python cbt_import_whole_vdi.py -ip <host address> -u <host username>
-p <host password> -v <vdi uuid> -f <import VDI filename>
"""

import urllib3
import requests
import XenAPI
import argparse

def create_new_vdi(session, sr, size):
    vdi_record = {
        "SR": sr,
        "virtual_size": size,
        "type": "user",
        "sharable": False,
        "read_only": False,
        "other_config": {},
        "name_label": "CBT backup"
    }
    vdi_ref = session.xenapi.VDI.create(vdi_record)
    vdi_uuid = session.xenapi.VDI.get_uuid(vdi_ref)
    return vdi_uuid


def import_vdi(host, session_id, vdi_uuid, file_format, import_path):
    url = ('https://%s/import_raw_vdi?session_id=%s&vdi=%s&format=%s'
           % (host, session_id, vdi_uuid, file_format))
    with open(import_path, 'r') as filehandle:
        # ToDo: Security - We need to verify the SSL certificate here.
        # Depends on CP-23051.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        with requests.Session() as session:
            request = session.put(url, filehandle, verify=False)
            request.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--host-ip', dest='host')
    parser.add_argument('-u', '--username', dest='username')
    parser.add_argument('-p', '--password', dest='password')
    parser.add_argument('-v', '--vdi-uuid', dest='vdi_uuid')
    parser.add_argument('-f', '--filename', dest='path')
    parser.add_argument('--as-new-vdi', dest='new_vdi', action='store_const',
                        const=True, default=False,
                        help='Create a new VDI for the import')
    args = parser.parse_args()

    session = XenAPI.Session("https://" + args.host, ignore_ssl=True)
    session.login_with_password(args.username, args.password, "0.1",
                                "CBT example")

    try:
        vdi_uuid = args.vdi_uuid
        if args.new_vdi:
            vdi_ref = session.xenapi.VDI.get_by_uuid(args.vdi_uuid)
            size = session.xenapi.VDI.get_virtual_size(vdi_ref)
            sr_ref = session.xenapi.VDI.get_SR(vdi_ref)
            vdi_uuid = create_new_vdi(session, sr_ref, size)

        import_vdi(args.host, session._session, vdi_uuid, 'raw',
                   args.path)
        print vdi_uuid
    finally:
        session.xenapi.session.logout(session)


if __name__ == "__main__":
    main()
