## dfo-hpc sample code

### Structure Overview
In order to run the Python samples, they must be updated with Azure Batch
and Azure Storage credentials. 

### Setting up the Python environment
In order to run the samples, you will need a Python interpreter compatible
with version 2.7 or 3.3+. You will also need to install the
[Azure Batch](https://pypi.python.org/pypi/azure-batch) and
[Azure Storage](https://pypi.python.org/pypi/azure-storage) python packages.
Installation can be performed using the [requirements.txt](./requirements.txt)
file via the command `pip install -r requirements.txt`

### MPI on Azure
Using infiniband is limited to certain instance types, and there is also the issue of having
the proper drivers and support for infiniband. CentOS is best, although Ubuntu 16 might be supported.

For more details on MPI/RDMA, visit [here](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/classic/rdma-cluster).


### Notice
Based on linux_mpi_task_demo.py - Batch Python tutorial sample for multi-instance
tasks in linux (OpenFoam application)
```
Copyright (c) Microsoft Corporation
All rights reserved.
MIT License
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```