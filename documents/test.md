# Index
* [Setup Test Environment](#setup-test-environment)
* [Run Unit Tests](#run-unit-tests)


# Setup Test Environment
```bash
# Assuming your current directory is project root
mkdir -p ~/.venvs/zworkflow_unit_test
python3 -m venv ~/.venvs/zworkflow_unit_test
source ~/.venvs/zworkflow_unit_test/bin/activate
pip install pip --upgrade
pip install -e .
pip install pytest pytest-cov pytest-asyncio testcontainers
```

# Run Unit Tests
```bash
# Run all unit tests
# Assuming your current directory is project root
source ~/.venvs/zworkflow_unit_test/bin/activate
pytest -m "not integration" -v -s --cov=zworkflow --cov-report=html tests/
```

# Run Integration Test

Please do not run zworkflow server while you are running integration test.

You need to modify file `sample_worker/zworkflow.yaml` to match your local environment

```bash
# Assuming your current directory is project root
source ~/.venvs/zworkflow_unit_test/bin/activate
CONFIG=$PWD/sample_worker/zworkflow.yaml VENV_DIR=~/.venvs/zworkflow_unit_test pytest -m "integration" -v -s --cov=zworkflow --cov-report=html tests/
```
