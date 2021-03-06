from __future__ import print_function
import datetime
import os
import sys
import coloredlogs, logging
import azure.storage.blob as azureblob
import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
import multi_task_helpers
import time
import configparser
from azure.storage.blob import BlockBlobService, BlobPermissions, ContainerPermissions
from azure.storage.common.retry import (
    ExponentialRetry,
    LinearRetry,
    no_retry,
)

def absoluteFilePaths(directory):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))


logger = logging.getLogger(__name__)

# Enable log output only for my logger
coloredlogs.install(level='DEBUG', logger=logger)

# Enable log output for ALL sources
#coloredlogs.install(level='DEBUG')


sys.path.append('.')
import common.helpers  # noqa


# Set these environment variables
# export _BATCH_ACCOUNT_KEY=abd123==
# etc
_BATCH_ACCOUNT_KEY = os.environ['_BATCH_ACCOUNT_KEY']
_BATCH_ACCOUNT_NAME = os.environ['_BATCH_ACCOUNT_NAME']
_BATCH_ACCOUNT_URL = os.environ['_BATCH_ACCOUNT_URL']

_STORAGE_ACCOUNT_NAME = os.environ['_STORAGE_ACCOUNT_NAME']
_STORAGE_ACCOUNT_KEY = os.environ['_STORAGE_ACCOUNT_KEY']

# Path to the jobs directory
JOB_PATH = './jobs/pingpong'

config = configparser.ConfigParser()
config.read(JOB_PATH + '/config.ini')



# Maximum time to run in minutes
MAX_RUNTIME = 30
_APP_NAME = 'pingpong'
_OS_NAME = config['node']['CFG_OS_NAME']
_POOL_ID = common.helpers.generate_unique_resource_name(
    'pool_{}_{}'.format(_OS_NAME, _APP_NAME))
_POOL_NODE_COUNT = config['node']['CFG_NODE_COUNT']
_POOL_VM_SIZE = config['node']['CFG_VM_SIZE']
_NODE_OS_PUBLISHER = config['node']['CFG_OS_PUBLISHER']
_NODE_OS_OFFER = config['node']['CFG_OS_OFFER']
_NODE_OS_SKU = config['node']['CFG_OS_SKU']

_POOL_INTERNODE = config['pool']['CFG_INTERNODE']

JOB_NAME = config['job']['JOB_NAME']


_JOB_ID = 'job-{}'.format(_POOL_ID)
_TASK_ID = common.helpers.generate_unique_resource_name(
    'task_{}_{}'.format(_OS_NAME, _APP_NAME))
_TASK_OUTPUT_FILE_PATH_ON_VM = '../std*.txt'
_TASK_OUTPUT_BLOB_NAME = 'stdout.txt'
_NUM_INSTANCES = _POOL_NODE_COUNT


if __name__ == '__main__':

    start_time = datetime.datetime.now().replace(microsecond=0)
    logger.info('Sample start: {}'.format(start_time))

    # Create the blob client, for use in obtaining references to
    # blob storage containers and uploading files to containers.

    blob_client = azureblob.BlockBlobService(
        account_name=_STORAGE_ACCOUNT_NAME, account_key=_STORAGE_ACCOUNT_KEY)
    # Can't get retry to work
    # TODO
    #blob_client.retry = LinearRetry(
    #    backoff=5, max_attempts=3, retry_to_secondary=False, random_jitter_range=3)

    # Use the blob client to create the containers in Azure Storage if they
    # don't yet exist.
    input_container_name = common.helpers.generate_unique_resource_name(
        'input-{}'.format(_APP_NAME))
    output_container_name = common.helpers.generate_unique_resource_name(
        'output-{}'.format(_APP_NAME))
    blob_client.create_container(input_container_name, fail_on_exist=False)
    blob_client.create_container(output_container_name, fail_on_exist=False)

    persistent_input_storage_sas = blob_client.generate_container_shared_access_signature(
        container_name="job-" + JOB_NAME, 
        permission=ContainerPermissions.READ + ContainerPermissions.LIST,
        expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=120)
        )
    persistent_input_storage_sas = 'https://{}.blob.core.windows.net/job-{}?{}'.format(
        _STORAGE_ACCOUNT_NAME, JOB_NAME, persistent_input_storage_sas)

    input_storage_sas = blob_client.generate_container_shared_access_signature(
        container_name=input_container_name, 
        permission=ContainerPermissions.READ + ContainerPermissions.LIST,
        expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=120)
        )
    input_storage_sas = 'https://{}.blob.core.windows.net/{}?{}'.format(
        _STORAGE_ACCOUNT_NAME, input_container_name, input_storage_sas)



    # Obtain a shared access signature that provides write access to the output
    # container to which the tasks will upload their output.
    output_container_sas = common.helpers.create_container_and_create_sas(
        blob_client,
        output_container_name,
        BlobPermissions.WRITE,
        expiry=None,
        timeout=120)

    output_container_sas = 'https://{}.blob.core.windows.net/{}?{}'.format(
        _STORAGE_ACCOUNT_NAME, output_container_name, output_container_sas)


    # Get all files in the shared subdirectory
    common_file_paths = absoluteFilePaths(JOB_PATH + '/shared')

    common_files = [
        common.helpers.upload_file_to_container(
            blob_client, input_container_name, os.path.realpath(file_path), timeout=120, path_prefix='shared/')
        for file_path in common_file_paths]

    # Command to run on all subtasks including primary before starting
    # application command on primary.
    coordination_cmdline = ['bash -c "./shared/prepare-all.sh"']

    # The collection of scripts/data files that are to be used/processed by
    # the task (used/processed by primary in a multiinstance task).
    input_file_paths = absoluteFilePaths(JOB_PATH + '/master')

    # Upload the script/data files to Azure Storage
    input_files = [
        common.helpers.upload_file_to_container(
            blob_client, input_container_name, file_path, timeout=120, path_prefix='master/')
        for file_path in input_file_paths]
    print ("input files debug is\n")
    print(input_files)

    # Main application command to execute multiinstance task on a group of
    # nodes, eg. MPI.
    application_cmdline = ['bash -c "./master/execute-master.sh {}"'.format(_NUM_INSTANCES)]

    if common.helpers.query_yes_no('Proceed with batch pool creation?') == 'no':
        raise SystemExit



    # Create a Batch service client.  We'll now be interacting with the Batch
    # service in addition to Storage
    credentials = batchauth.SharedKeyCredentials(_BATCH_ACCOUNT_NAME, _BATCH_ACCOUNT_KEY)
    batch_client = batch.BatchServiceClient(credentials, _BATCH_ACCOUNT_URL)

    # Create the pool that will contain the compute nodes that will execute the
    # tasks. The resource files we pass in are used for configuring the pool's
    # start task, which is executed each time a node first joins the pool (or
    # is rebooted or re-imaged).
    multi_task_helpers.create_pool_and_wait_for_vms(
        batch_client, _POOL_ID, _NODE_OS_PUBLISHER, _NODE_OS_OFFER,
        _NODE_OS_SKU, _POOL_VM_SIZE, _POOL_NODE_COUNT, enable_inter_node_communication=_POOL_INTERNODE,
        command_line=coordination_cmdline,
        resource_files=[batch.models.ResourceFile(storage_container_url=persistent_input_storage_sas),
            batch.models.ResourceFile(storage_container_url=input_storage_sas)],
        elevation_level=batchmodels.ElevationLevel.admin)

    # Create the job that will run the tasks.
    common.helpers.create_job(batch_client, _JOB_ID, _POOL_ID)

    # Add the tasks to the job.  We need to supply a container shared access
    # signature (SAS) token for the tasks so that they can upload their output
    # to Azure Storage.
    multi_task_helpers.add_task(
        batch_client, _JOB_ID, _TASK_ID, _NUM_INSTANCES,
        common.helpers.wrap_commands_in_shell(_OS_NAME, application_cmdline),
        input_files, batchmodels.ElevationLevel.admin,
        _TASK_OUTPUT_FILE_PATH_ON_VM, output_container_sas,
        common.helpers.wrap_commands_in_shell(_OS_NAME, coordination_cmdline),
        common_files)

    # Pause execution until task (and all subtasks for a multiinstance task)
    # reach Completed state.
    multi_task_helpers.wait_for_tasks_to_complete(
        batch_client, _JOB_ID, datetime.timedelta(minutes=MAX_RUNTIME))

    print("Success! Task reached the 'Completed' state within the specified timeout period.")

    # Print out some timing info
    end_time = datetime.datetime.now().replace(microsecond=0)
    
    logger.info('Sample end: {}'.format(end_time))
    logger.info('Elapsed time: {}'.format(end_time - start_time))
    
    # You have to give some time for the results to transfer before you kill things
    logger.info("Sleeping 15 seconds...")
    time.sleep(15)
    
    common.helpers.query_yes_no('Ready to proceed to deletion?')

    logger.info('Deleting input container...')
    #blob_client.delete_container(input_container_name)

    logger.info('Deleting job and pool...')
    batch_client.job.delete(_JOB_ID)
    batch_client.pool.delete(_POOL_ID)

    # Download the task output files from the output Storage container to a
    # local directory
    if common.helpers.query_yes_no('Download results?') == 'yes':
        downloadPath = os.path.expanduser('~') + "/" + output_container_name
        logger.info('Downloading results to ' + downloadPath)
        os.mkdir(os.path.expanduser('~') + "/" + output_container_name)
        common.helpers.download_blob_from_container(
            blob_client,
            output_container_name,
            _TASK_OUTPUT_BLOB_NAME,
            downloadPath)

    logger.info("Done!")