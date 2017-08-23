#!/usr/bin/env python

"""
For a given vdi and import file this script will import a VDI on to a XS host. This script needs to be run whenever you want to restore a VDI to a previous version.

example: python cbt_import_whole_vdi.py -h <host address> -u <host username> -p <host password> -v <vdi uuid> -f <import VDI filename>
"""

import urllib3
import requests
import XenAPI
import argparse

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
    args = parser.parse_args()

    session = XenAPI.Session("https://" + args.host, ignore_ssl=True)
    session.login_with_password(args.username, args.password, "0.1", "CBT example")

    try:
        import_vdi(args.host, session._session, args.vdi_uuid, 'raw', args.path)
    finally:
        session.xenapi.session.logout(session)


if __name__ == "__main__":
    main()
