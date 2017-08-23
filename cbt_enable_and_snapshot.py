#!/usr/bin/env python

"""
For a given VDI this script enables cbt, snapshots the VDI and exports the snapshot. This script will only need to be run once when first enabling cbt backups and will create the base snapshot. After the VDI has been exported the snapshot data is destroyed to save space on the host.

example: python cbt_enable_and_snapshot.py -h <host address> -u <host username> -p <host password> -v <vdi uuid> -o <output path of VDI>

Script will then print out the snapshot uuid before it returns. VDI is saved to the output path specified
"""

import XenAPI
import shutil
import urllib3
import requests
import argparse

def export_vdi(host, session_id, vdi_uuid, file_format, export_path):
    url = ('https://%s/export_raw_vdi?session_id=%s&vdi=%s&format=%s'
           % (host, session_id, vdi_uuid, file_format))
    with requests.Session() as session:
        # ToDo: Security - We need to verify the SSL certificate here.
        # Depends on CP-23051.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        request = session.get(url, verify=False, stream=True)
        with open(export_path, 'wb') as filehandle:
            shutil.copyfileobj(request.raw, filehandle)
        request.raise_for_status()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--host-ip', dest='host')
    parser.add_argument('-u', '--username', dest='username')
    parser.add_argument('-p', '--password', dest='password')
    parser.add_argument('-v', '--vdi-uuid', dest='vdi_uuid')
    parser.add_argument('-o', '--output-path', dest='output_path')
    args = parser.parse_args()
    
    session = XenAPI.Session("https://" + args.host, ignore_ssl=True)
    session.login_with_password(args.username, args.password, "0.1", "CBT example")
    
    try:
        vdi_ref = session.xenapi.VDI.get_by_uuid(args.vdi_uuid)
        session.xenapi.VDI.enable_cbt(vdi_ref)
        snapshot_ref = session.xenapi.VDI.snapshot(vdi_ref)
        export_vdi(args.host, session._session, session.xenapi.VDI.get_uuid(snapshot_ref), 'raw', args.output_path)
        # Once you are done copying the blocks, delete the snapshot data
        session.xenapi.VDI.data_destroy(snapshot_ref)
        print session.xenapi.VDI.get_uuid(snapshot_ref)
    
    finally:
        session.xenapi.session.logout()

if __name__ == "__main__":
    main()
