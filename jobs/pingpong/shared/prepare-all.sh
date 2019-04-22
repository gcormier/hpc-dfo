#set -e
#set -o

echo PREPARE RUNNING $AZ_BATCH_NODE_ID
echo AZ_BATCH_IS_CURRENT_NODE_MASTER=$AZ_BATCH_IS_CURRENT_NODE_MASTER

echo AZ_BATCH_NODE_ROOT_DIR=$AZ_BATCH_NODE_ROOT_DIR
echo AZ_BATCH_NODE_SHARED_DIR=$AZ_BATCH_NODE_SHARED_DIR
echo AZ_BATCH_NODE_STARTUP_DIR=$AZ_BATCH_NODE_STARTUP_DIR

echo AZ_BATCH_TASK_DIR=$AZ_BATCH_TASK_DIR
echo AZ_BATCH_TASK_SHARED_DIR=$AZ_BATCH_TASK_SHARED_DIR
echo AZ_BATCH_TASK_WORKING_DIR=$AZ_BATCH_TASK_WORKING_DIR

pwd

# Requirements
yum -y install epel-release
yum -y install gfortran cmake git makedepf90 gcc netcdf netcdf-devel netcdf-fortran-devel netcdf-fortran netcdf-static mpich-3.0 mpich-3.0-devel netcdf-fortran-mpich netcdf-fortran-mpich-devel hdf5-mpich hdf5-mpich-devel
export PATH=$PATH:/usr/lib64/mpich/bin/
