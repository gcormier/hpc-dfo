
#pingpong over TCP

#export PATH=$PATH:/usr/lib64/openmpi/bin/
#mpicc pingpong.c -o pingpong

#mpirun -n $1 -ppn `nproc` -hosts $AZ_BATCH_HOST_LIST IMB-MPI1 pingpong

#echo HOSTS are $AZ_BATCH_HOST_LIST

#echo 1
#mpirun --host $AZ_BATCH_HOST_LIST -np 2 pingpong

#echo 2
#/bin/bash -c mpirun --host $AZ_BATCH_HOST_LIST -np 2 pingpong


#echo 3
#mpirun --host $AZ_BATCH_HOST_LIST pingpong

echo JOB RUNNING $AZ_BATCH_NODE_ID
#pwd
#ls
#ls /usr/lib64/openmpi/bin/

#/usr/lib64/openmpi/bin/mpicc pingpong.c