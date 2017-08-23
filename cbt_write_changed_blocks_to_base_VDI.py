#!/usr/bin/env python

"""
For a given base VDI and set of changed blocks this script will construct a new VDI which contains the changed blocks. This script will be run before restoring the host VDI to create a VDI which includes all the blocks up to the point in time you wish to restore to. As this script only applies one set changed blocks at a time it may need to be run multiple times if you have had a number of snapshots.

example: python cbt_write_changed_blocks_to_base_VDI.py -v <base VDI path> -b <bitmap path> -c <changed blocks path> -o <output VDI path>

Script will output a VDI to the output path specified.
"""

import argparse

# CBT tracks 64KB blocks. Therefore each bit in the bitmap corresponds to a 64KB block on the VDI.
changed_block_size = 64 * 1024

def write_changed_blocks_to_base_VDI(vdi_path, changed_block_path, bitmap_path, output_path):
    bitmap = open(bitmap_path, 'r')
    vdi = open(vdi_path, 'r+b')
    blocks = open(changed_block_path, 'r+b')
    combined_vdi = open(output_path, 'wb')

    try:
        bitmap_r = bitmap.read()
        cb_offset = 0
        for x in range(0, len(bitmap_r)):
            offset = x * changed_block_size
            if bitmap_r[x] == "1":
                blocks.seek(cb_offset)
                blocks_r = blocks.read(changed_block_size)
                combined_vdi.write(blocks_r)
                cb_offset += changed_block_size
            else:
                vdi.seek(offset)
                vdi_r = vdi.read(changed_block_size)
                combined_vdi.write(vdi_r)
    finally:
        bitmap.close()
        vdi.close()
        blocks.close()
        combined_vdi.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vdi-base', dest='vdi_base')
    parser.add_argument('-b', '--bitmap', dest='bitmap')
    parser.add_argument('-c', '--changed-blocks', dest='changed_blocks')
    parser.add_argument('-o', '--output', dest='output')
    args = parser.parse_args()

    base_vdi_path = args.vdi_base
    changed_blocks_path = args.changed_blocks
    bitmap_path = args.bitmap
    output_path = args.output
    
    write_changed_blocks_to_base_VDI(args.vdi_base, args.changed_blocks, args.bitmap, args.output)

if __name__ == "__main__":
    main()
