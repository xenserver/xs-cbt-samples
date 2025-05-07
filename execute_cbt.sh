#!/bin/bash
set -eux
#This script runs the end-to-end cbt scripts
#example: ./execute_cbt.sh <host address> <username> <password> <vdi uuid> <vm uuid>

HOST=$1
USERNAME=$2
PASSWORD=$3
VDI=$4
VM=$5

BASE_VDI_PATH="./testvdi.raw"
BITMAP_PATH="./bitmap"
CHANGED_BLOCK_PATH="./testblocks.raw"
COMBINED_VDI_PATH="./testcombined.raw"
METADATA_PATH="./metadata"
CONNECTION="-ip $HOST -u $USERNAME -p $PASSWORD"

echo "Enabling CBT and exporting snapshot"
BASE_SNAPSHOT_UUID=$(python3 cbt_enable_and_snapshot.py $CONNECTION -v $VDI -o $BASE_VDI_PATH)
echo $BASE_SNAPSHOT_UUID

echo "Exporting VM metadata"
python3 cbt_vm_metadata_export.py $CONNECTION -v $VM -o $METADATA_PATH

echo "Taking new snapshot and exporting changed blocks"
OUTPUT=$(python3 cbt_export_changes.py $CONNECTION -v $VDI -s $BASE_SNAPSHOT_UUID -co $CHANGED_BLOCK_PATH -bo $BITMAP_PATH)
echo ${OUTPUT##* } 

echo "Writing changed blocks to base VDI"
python3 cbt_write_changed_blocks_to_base_VDI.py -v $BASE_VDI_PATH -b $BITMAP_PATH -c $CHANGED_BLOCK_PATH -o $COMBINED_VDI_PATH

echo "Importing new VDI back to host"
NEW_VDI=$(python3 cbt_import_whole_vdi.py $CONNECTION -v $VDI -f $COMBINED_VDI_PATH --as-new-vdi)
echo $NEW_VDI

echo "Importing metadata to host"
python3 cbt_vm_metadata_import.py $CONNECTION -v $VM -i $METADATA_PATH $VDI $NEW_VDI
