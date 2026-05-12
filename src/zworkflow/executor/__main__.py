from zworkflow.app_config import app_config
import logging.config
logging.config.dictConfig(app_config.logging)

import logging
logger = logging.getLogger(__name__)

import argparse
import signal
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import workflow
from temporalio.worker import UnsandboxedWorkflowRunner
import yaml
from .generic_workflow import GenericWorkflow
from .activities import greet, generic_activity
from .task_map import generate_task_map

#######################################################################################
# This is temporal worker
#######################################################################################
async def shutdown_handler(worker):
    await worker.shutdown()
    print("Worker shutdown gracefully!")

async def main():
    parser = argparse.ArgumentParser(description='ZWorkflow Temporal Worker')
    parser.add_argument('--handlers', required=True, help='Path to task handler definition YAML file')
    args = parser.parse_args()

    with open(args.handlers, "rt") as f:
        task_handler_config = yaml.safe_load(f)
    generate_task_map(task_handler_config)

    logger.info(f"temporal config: host  = {app_config.temporal.host}")
    logger.info(f"temporal config: port  = {app_config.temporal.port}")
    logger.info(f"temporal config: queue = {app_config.temporal.queue_name}")

    client = await Client.connect(f"{app_config.temporal.host}:{app_config.temporal.port}")
    worker = Worker(
        client,
        task_queue=app_config.temporal.queue_name,
        workflows=[GenericWorkflow],
        activities=[generic_activity],
        workflow_runner=UnsandboxedWorkflowRunner(),
        debug_mode=True
    )
    
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(
        signal.SIGTERM,
        lambda: asyncio.create_task(shutdown_handler(worker))
    )
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: asyncio.create_task(shutdown_handler(worker))
    )
    logger.info(f"temporal worker started")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
