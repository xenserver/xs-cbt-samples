#!/usr/bin/env python3

"""
For a given VDI and previous snapshot uuid this script will take a new
snapshot, find the changed blocks since the previous snapshot and then export
the changed blocks via nbd. This script will need to be run everytime you wish
to take a new snapshot. After the changed blocks have been exported the
snapshot data is destroyed to save space on the host.

This script utilises the core of the new CBT functionality which is to find
changes blocks between snapshots and exporting them via NBD.

example: python cbt_export_changes.py -ip <host address> -u <host username>
-p <host password> -v <vdi uuid> -s <previous snapshot uuid>
-co <changed block output path> -bo <bitmap output path>

Script will then print out the new snapshot uuid at the end. Changed blocks
and bitmap are saved to the paths specified.
"""

import XenAPI
from nbd_client import new_nbd_client
import base64
from bitstring import BitStream
import argparse
import os
import re
import sys

# CBT tracks 64KB blocks. Therefore each bit in the bitmap corresponds to a
# 64KB block on the VDI.
changed_block_size = 64 * 1024
certfile = "cacert.pem"


def get_cert_subject(cert_text):
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert = x509.load_pem_x509_certificate(cert_text.encode(), default_backend())
    try:
        value_types = [x509.DNSName, x509.GeneralName, x509.RFC822Name]
        for value_type in value_types:
            ext = cert.extensions.get_extension_for_oid(
                          x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            cert_subject = ext.value.get_values_for_type(value_type)[0]
            if cert_subject:
                return cert_subject
        raise Exception

    except:
        sub = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        cert_subject = sub[0].value
        if cert_subject:
            return cert_subject
        else:
            print("Could not find the subject for the certificate. Exiting")
            sys.exit(1)


def delete_host_certificates_file():
    os.remove(certfile)


def get_changed_blocks(host, export_name, tls_subject, bitmap, bitmap_output_path):
    bitmap = BitStream(bytes=base64.b64decode(bitmap))
    with open(bitmap_output_path, 'ab') as bit_out:
        for bit in bitmap:
            if int(bit) == 1 or int(bit) == 0:
                # The bits are written in the form "0" and "1" to the file
                bit_out.write(str(int(bit)).encode())
    print("connecting to NBD")
    client = new_nbd_client(host, export_name, certfile, tls_subject)
    print("size: %s" % client.size())
    for i in range(0, len(bitmap)):
        if bitmap[i] == 1:
            offset = i * changed_block_size
            print("reading %d bytes from offset %d" % (changed_block_size,
                                                       offset))
            data = client.read(offset=offset, length=changed_block_size)
            yield data
    print("closing NBD")
    client.close()


def save_changed_blocks(changed_blocks, output_file):

    with open(output_file, 'ab') as out:
        for b in changed_blocks:
            out.write(b)


def download_changed_blocks(bitmap, nbd_info, changed_blocks_output_path,
                            bitmap_output_path):

    print("downloading changed blocks")
    cert_text = nbd_info['cert']
    with open(certfile, 'w') as cert_out:
        cert_out.write(cert_text)
    tls_subject = get_cert_subject(cert_text)
    host = nbd_info['address']
    uri = nbd_info['exportname']
    blocks = get_changed_blocks(host, uri, tls_subject, bitmap, bitmap_output_path)
    save_changed_blocks(blocks, changed_blocks_output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--host-ip', dest='host')
    parser.add_argument('-u', '--username', dest='username')
    parser.add_argument('-p', '--password', dest='password')
    parser.add_argument('-v', '--vdi-uuid', dest='vdi_uuid')
    parser.add_argument('-s', '--snapshot-uuid', dest='snapshot_uuid')
    parser.add_argument('-co', '--changed-blocks-output-path',
                        dest='changed_blocks_output_path')
    parser.add_argument('-bo', '--bitmap-output-path',
                        dest='bitmap_output_path')
    args = parser.parse_args()

    session = XenAPI.Session("https://" + args.host, ignore_ssl=True)
    session.login_with_password(args.username, args.password, "0.1",
                                "CBT example")

    try:
        vdi_ref = session.xenapi.VDI.get_by_uuid(args.vdi_uuid)
        last_snapshot_ref = session.xenapi.VDI.get_by_uuid(args.snapshot_uuid)
        new_snapshot_ref = session.xenapi.VDI.snapshot(vdi_ref)
        bitmap = session.xenapi.VDI.list_changed_blocks(last_snapshot_ref,
                                                          new_snapshot_ref)
        # get_nbd_info may return the details for multiple addresses, for this
        # example we will just use the first one
        nbd_info = session.xenapi.VDI.get_nbd_info(new_snapshot_ref)[0]
        download_changed_blocks(bitmap, nbd_info,
                        args.changed_blocks_output_path,
                        args.bitmap_output_path)
        # Once you are done copying the blocks you want you can delete the
        # snapshot data
        session.xenapi.VDI.data_destroy(new_snapshot_ref)
        print(session.xenapi.VDI.get_uuid(new_snapshot_ref))
    finally:
        session.xenapi.session.logout(session)
        delete_host_certificates_file()


if __name__ == "__main__":
    main()
