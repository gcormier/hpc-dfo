#set -e  # Abort script if anything fails (non zero return)
set -o  # Command echo

echo PREPARE RUNNING $AZ_BATCH_NODE_ID
echo AZ_BATCH_IS_CURRENT_NODE_MASTER=$AZ_BATCH_IS_CURRENT_NODE_MASTER

echo AZ_BATCH_NODE_ROOT_DIR=$AZ_BATCH_NODE_ROOT_DIR
echo AZ_BATCH_NODE_SHARED_DIR=$AZ_BATCH_NODE_SHARED_DIR
echo AZ_BATCH_NODE_STARTUP_DIR=$AZ_BATCH_NODE_STARTUP_DIR

echo AZ_BATCH_TASK_DIR=$AZ_BATCH_TASK_DIR
echo AZ_BATCH_TASK_SHARED_DIR=$AZ_BATCH_TASK_SHARED_DIR
echo AZ_BATCH_TASK_WORKING_DIR=$AZ_BATCH_TASK_WORKING_DIR
echo AZ_BATCH_HOST_LIST=$AZ_BATCH_HOST_LIST

echo Current working directory is `pwd`

# Requirements
yum -y install epel-release
yum -y install gfortran cmake git makedepf90 gcc netcdf netcdf-devel netcdf-fortran-devel netcdf-fortran netcdf-static mpich-3.0 mpich-3.0-devel netcdf-fortran-mpich netcdf-fortran-mpich-devel hdf5-mpich hdf5-mpich-devel
export PATH=$PATH:/usr/lib64/mpich/bin/

mpicc pingpong.c -o pingpong

source /opt/intel/impi/5.1.3.223/bin64/mpivars.sh

chmod -R 777 /mnt

export I_MPI_FABRICS=shm:dapl
export I_MPI_DAPL_PROVIDER=ofa-v2-ib0
export I_MPI_DYNAMIC_CONNECTION=0

mpirun IMB-MPI1 pingpong > pong1.log
echo "----"
mpirun -n 2 ./pingpong > pong2.log

echo All done!
exit 0