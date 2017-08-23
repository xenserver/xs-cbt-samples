# cbt_user_scripts
This repository contains a collection of scripts that utilise the XenServer changed block tracking API. 

These scripts serve as example of how to use the feature end-to-end including enabling cbt, copying changed blocks and destroying unnecessary snapshot data.

The examples are written in python.

# License
This code is licensed under the BSD 3-Clause license. Please see the LICENSE file for more information

# How to use these scripts
The required python packages used can be found in the requirements.txt file. Note that depending on the distro you are using some of these packages may already be installed.

For the XenAPI package use the one provided in the SDK. 

The end-to-end scripts can then be run using:
./execute-cbt.sh \<host address> \<username> \<password> \<VDI uuid>
