# XenServer CBT sample code
This repository contains a collection of scripts that use the XenServer changed block tracking API. 

These scripts are an example of how to use the changed block tracking feature from end-to-end including:
* enabling changed block tracking
* copying changed blocks
* destroying unnecessary snapshot data.

The examples are written in Python.

# License
This code is licensed under the BSD 3-Clause license. Please see the [LICENSE](LICENSE) file for more information.

# How to use these scripts
The required Python packages used can be found in the [requirements.txt](requirements.txt) file. Note that depending on the distro you are using some of these packages may already be installed.

For the XenAPI package use the one provided in the SDK. 

You can then run the end-to-end scripts using:
```bash
    ./execute-cbt.sh <host address> <username> <password> <VDI uuid>
```
