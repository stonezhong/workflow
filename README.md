# Index
* [Brief](#brief)
* [Getting Started](#getting-started)
    * [Step 1: Create PostgreSQL Server](#step-1-create-postgresql-server)
    * [Step 2: Download and run temporal dev server](#step-2-download-and-run-temporal-dev-server)
    * [Step 3: Start ZWorkflow](#step-3-start-zworkflow)
    * [Step 4: define 2 sample tasks](#step-4-define-2-sample-tasks)
    * [Step 5: Define a test workflow](#step-5-define-a-test-workflow)
    * [Step 6: Start sample workflow](#step-6-start-sample-workflow)

# Brief
ZWorkflow is a workflow manager, it allows you to build workflow without wrting code.

# Getting Started
## Step 1: Create PostgreSQL Server
```bash
docker volume create pgdata
docker run -d \
  --name postgres \
  -e POSTGRES_USER=zworkflow \
  -e POSTGRES_PASSWORD=foobar \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16
```
## Step 2: Download and run temporal dev server
```bash
# If your CPU is x64 compatible
wget -O temporal 'https://temporal.download/cli/archive/latest?platform=linux&arch=amd64'
sudo mv temporal /usr/local/bin

# If you are using macos
brew install temporal

# then you can start temporal
temporal server start-dev --ip 0.0.0.0
```

## Step 3: Start ZWorkflow

filename: demo_handlers.py
```python
from typing import Callable
import asyncio

async def add(input: dict, logger=Callable[[str],None]) -> dict:
    await asyncio.sleep(5)
    # raise RuntimeError("Oops")
    logger(f"adding {input['x']} and {input['y']}")
    return {"result": input['x'] + input['y']}


async def mul(input: dict, logger=Callable[[str], None]) -> dict:
    await asyncio.sleep(8)
    return {"result": input['x'] * input['y']}
```

handlers.yaml
```yaml
add:
  "1.0": demo_handlers:add
mul:
  "1.0": demo_handlers:mul
```

zworkflow.yaml
```yaml
logging:
  version: 1
  disable_existing_loggers: false
  formatters:
    standard:
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    console:
      class: logging.StreamHandler
      formatter: standard
      stream: ext://sys.stdout
    file:
      class: logging.FileHandler
      formatter: standard
      filename: /root/zworkflow.log
      encoding: utf-8
  loggers:
    sqlalchemy.engine:
      level: WARNING
    uvicorn.access:
      level: WARNING
    temporalio.worker:
      level: WARNING
    temporalio.activity:
      level: WARNING
  root:
    level: DEBUG
    handlers: [console, file]

database:
  url: postgresql+psycopg2://zworkflow:foobar@host.docker.internal:5432/mydb
  connect_args: {}
  create_tables: True

temporal:
  host: host.docker.internal
  port: 7233
  queue_name: my-task-queue
```

Dockerfile
```text
FROM --platform=linux/amd64 python:3.12

WORKDIR /root

RUN python3 -m pip install pip --upgrade
RUN python3 -m pip install zworkflow
COPY zworkflow.yaml /root
COPY handlers.yaml /root
COPY demo_handlers.py /root
```

Now build docker image:
```bash
docker build -t zworkflow .
```

Now, start zworkflow server:
```bash
docker run --name zworkflow --rm -p 8000:8000 -it zworkflow bash
uvicorn zworkflow.apis:app --host 0.0.0.0
```

Now start worker:
```bash
docker exec -it zworkflow bash
```
## Step 4: define 2 sample tasks
* Open [ZWorkflow WebUI](http://localhost:8000/webui)
* Click "New Task Definition"
    * set name to "add"
    * set version to "1.0"
    * set title to "add"
    * set description to "add"
    * set input schema to below
    ```yaml
    type: object
    required:
    - x
    - y
    properties:
    x:
        type: integer
    y:
        type: integer
    ```
    * set output schema to below:
    ```yaml
    type: object
    required:
    - result
    properties:
        result:
        type: integer
    ```
* Click "New Task Definition"
    * set name to "mul"
    * set version to "1.0"
    * set title to "mul"
    * set description to "multiply"
    * set input schema to below
    ```yaml
    type: object
    required:
    - x
    - y
    properties:
    x:
        type: integer
    y:
        type: integer
    ```
    * set output schema to below:
    ```yaml
    type: object
    required:
    - result
    properties:
        result:
        type: integer
    ```
![Create Task Definition](./documents/images/create_task_def_add.png)
![Create Task Definition](./documents/images/create_task_def_mul.png)

## Step 5: Define a test workflow

* Click "New Workflow Def"
    * set name to "test"
    * set version to "1.0"
    * set title to "test"
    * set description to "test workflow"
    * add step 1
        * set key to "step1"
        * set title to "Step 1"
        * set type to "TASK"
        * set Task Definition to "add v1.0"
        * set description to "add a and b"
        * set input to <code>{"x": workflow.input.a, "y": workflow.input.b}</code>
        * click "Add Step"
    * add step 2
        * set key to "step2"
        * set title to "Step 2"
        * set type to "TASK"
        * set Task Definition to "add v1.0"
        * set description to "add c and d"
        * set input to <code>{"x": workflow.input.c, "y": workflow.input.d}</code>
        * click "Add Step"
    * add step 3
        * set key to "step3"
        * set title to "Step 3"
        * set type to "TASK"
        * set Task Definition to "mul v1.0"
        * set description to "mul"
        * set input to <code>{"x": steps.step1.output.result, "y": steps.step2.output.result}</code>
        * Check "Return" checkbox
        * click "Add Step"
    * Add Step Dependency
        * click "Add Dependency", select "from" as step1, select to as step 3
        * click "Add Dependency", select "from" as step2, select to as step 3
    * Click "Create Workflow Definition"
![Create Workflow](./documents/images/create_workflow_def_overall.png)
![Create Workflow Step 1](./documents/images/create_workflow_def_step1.png)
![Create Workflow Step 2](./documents/images/create_workflow_def_step2.png)
![Create Workflow Step 3](./documents/images/create_workflow_def_step3.png)
![Create Workflow Step 4](./documents/images/create_workflow_def_add_dep.png)

## Step 6: Start sample workflow
* Click "New Workflow"
* Select "test v1.0" as workflow definition
* set title to "test"
* set description to "test"
* set input to <code>{"a": 1, "b": 2, "c": 3, "d": 4}</code>
* Click "Create Workflow"
![Create Workflow](./documents/images/create_workflow.png)

After you click "Create Workflow", you can watch the execution of this workflow
![View Workflow](./documents/images/workflow_1.png)
![View Workflow](./documents/images/workflow_2.png)
