## Azure Batch Python Article Samples

### Configuring the samples
In order to run the Python samples, they must be updated with Azure Batch
and Azure Storage credentials. 

### Setting up the Python environment
In order to run the samples, you will need a Python interpreter compatible
with version 2.7 or 3.3+. You will also need to install the
[Azure Batch](https://pypi.python.org/pypi/azure-batch) and
[Azure Storage](https://pypi.python.org/pypi/azure-storage) python packages.
Installation can be performed using the [requirements.txt](./requirements.txt)
file via the command `pip install -r requirements.txt`

### MPI sample
The MPI sample is an introduction to running an MPI command in Azure Batch in a
Linux environment. It creates a pool with RDMA enabled virtual machines (You can
use STANDARD_A8 to replace the virtual machine size if you don't have enough
core quota). It submits a job to the pool, and then submits a task which 
performs a simple MPI pingpong command. The files required by the task are
automatically uploaded to Azure Storage and then downloaded onto the nodes via
Batch resource files. When the task is done, the console output of the MPI
pingpong command is uploaded back to Azure Storage.

For more details on MPI/RDMA, visit [here](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/classic/rdma-cluster).


### Copyright
# linux_mpi_task_demo.py - Batch Python tutorial sample for multi-instance
# tasks in linux (OpenFoam application)
#
# Copyright (c) Microsoft Corporation
#
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.