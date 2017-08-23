#!/bin/bash
set -eux
#This script runs the end-to-end cbt scripts
#example: ./execute_cbt.sh <host address> <username> <password> <vdi uuid>

HOST=$1
USERNAME=$2
PASSWORD=$3
VDI=$4

BASE_VDI_PATH="./testvdi.vhd"
BITMAP_PATH="./bitmap"
CHANGED_BLOCK_PATH="./testblocks.vhd"
COMBINED_VDI_PATH="./testcombined"
CONNECTION="-ip $HOST -u $USERNAME -p $PASSWORD"

echo "Enabling CBT and exporting snapshot"
BASE_SNAPSHOT_UUID=$(python cbt_enable_and_snapshot.py $CONNECTION -v $VDI -o $BASE_VDI_PATH)
echo $BASE_SNAPSHOT_UUID

echo "Taking new snapshot and exporting changed blocks"
OUTPUT=$(python cbt_export_changes.py $CONNECTION -v $VDI -s $BASE_SNAPSHOT_UUID -co $CHANGED_BLOCK_PATH -bo $BITMAP_PATH)
echo ${OUTPUT##* } 

echo "Writing changed blocks to base VDI"
python cbt_write_changed_blocks_to_base_VDI.py -v $BASE_VDI_PATH -b $BITMAP_PATH -c $CHANGED_BLOCK_PATH -o ./testcombined.vhd

echo "Importing new VDI back to host"
python cbt_import_whole_vdi.py $CONNECTION -v $VDI -f ./testcombined.vhd
