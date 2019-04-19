from __future__ import print_function
import datetime
import os
import sys
import coloredlogs, logging


try:
    input = raw_input
except NameError:
    pass

import azure.storage.blob as azureblob
import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
import multi_task_helpers
import time

from azure.storage.common.retry import (
    ExponentialRetry,
    LinearRetry,
    no_retry,
)

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

_POOL_INTERNODE = True

# Maximum time to run in minutes
MAX_RUNTIME = 30


_OS_NAME = 'linux'
_APP_NAME = 'pingpong'
_POOL_ID = common.helpers.generate_unique_resource_name(
    'pool_{}_{}'.format(_OS_NAME, _APP_NAME))
_POOL_NODE_COUNT = 2
_POOL_VM_SIZE = 'STANDARD_H16r'
#_POOL_VM_SIZE = 'Standard_F4s_v2'
_NODE_OS_PUBLISHER = 'OpenLogic'
_NODE_OS_OFFER = 'CentOS-HPC'
_NODE_OS_SKU = '7.4'
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
    blob_client.retry = LinearRetry(
        backoff=5, max_attempts=3, retry_to_secondary=False, random_jitter_range=3)

    # Use the blob client to create the containers in Azure Storage if they
    # don't yet exist.
    input_container_name = common.helpers.generate_unique_resource_name(
        'input-{}-{}'.format(_OS_NAME, _APP_NAME))
    output_container_name = common.helpers.generate_unique_resource_name(
        'output-{}-{}'.format(_OS_NAME, _APP_NAME))
    blob_client.create_container(input_container_name, fail_on_exist=False)
    blob_client.create_container(output_container_name, fail_on_exist=False)

    # Obtain a shared access signature that provides write access to the output
    # container to which the tasks will upload their output.
    output_container_sas = common.helpers.create_container_and_create_sas(
        blob_client,
        output_container_name,
        azureblob.BlobPermissions.WRITE,
        expiry=None,
        timeout=120)

    output_container_sas = 'https://{}.blob.core.windows.net/{}?{}'.format(
        _STORAGE_ACCOUNT_NAME, output_container_name, output_container_sas)

    # The collection of common scripts/data files that are to be
    # used/processed by all subtasks (including primary) in a
    # multi-instance task.
    common_file_paths = [
        os.path.realpath('./data/coordination-cmd')]

    # Upload the common script/data files to Azure Storage
    common_files = [
        common.helpers.upload_file_to_container(
            blob_client, input_container_name, file_path, timeout=120)
        for file_path in common_file_paths]

    # Command to run on all subtasks including primary before starting
    # application command on primary.
    coordination_cmdline = ['$AZ_BATCH_TASK_SHARED_DIR/coordination-cmd']

    # The collection of scripts/data files that are to be used/processed by
    # the task (used/processed by primary in a multiinstance task).
    input_file_paths = [
        os.path.realpath('./data/application-cmd')]

    # Upload the script/data files to Azure Storage
    input_files = [
        common.helpers.upload_file_to_container(
            blob_client, input_container_name, file_path, timeout=120)
        for file_path in input_file_paths]

    # Main application command to execute multiinstance task on a group of
    # nodes, eg. MPI.
    application_cmdline = [
        '$AZ_BATCH_TASK_WORKING_DIR/application-cmd {}'.format(_NUM_INSTANCES)]

    # Create a Batch service client.  We'll now be interacting with the Batch
    # service in addition to Storage
    credentials = batchauth.SharedKeyCredentials(
        _BATCH_ACCOUNT_NAME, _BATCH_ACCOUNT_KEY)
    batch_client = batch.BatchServiceClient(credentials, _BATCH_ACCOUNT_URL)

    # Create the pool that will contain the compute nodes that will execute the
    # tasks. The resource files we pass in are used for configuring the pool's
    # start task, which is executed each time a node first joins the pool (or
    # is rebooted or re-imaged).
    multi_task_helpers.create_pool_and_wait_for_vms(
        batch_client, _POOL_ID, _NODE_OS_PUBLISHER, _NODE_OS_OFFER,
        _NODE_OS_SKU, _POOL_VM_SIZE, _POOL_NODE_COUNT, enable_inter_node_communication=_POOL_INTERNODE)

    # Create the job that will run the tasks.
    common.helpers.create_job(batch_client, _JOB_ID, _POOL_ID)

    # Add the tasks to the job.  We need to supply a container shared access
    # signature (SAS) token for the tasks so that they can upload their output
    # to Azure Storage.
    multi_task_helpers.add_task(
        batch_client, _JOB_ID, _TASK_ID, _NUM_INSTANCES,
        common.helpers.wrap_commands_in_shell(_OS_NAME, application_cmdline),
        input_files, batchmodels.ElevationLevel.non_admin,
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
    

    logger.info('Deleting input container...')
    blob_client.delete_container(input_container_name)

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
    