# Build Enhancement Tools

> TODO: Add brief description of build enhancement tools.

## Prepare Python environment

Start a new virtual Python environment, only need to be done once.

```bash
cd path/to/current/project/root
virutalenv -p python3.6 .env
```

> NOTE: path to current project root just means current project root directory, not Android project root directory that usually contains directory `.repo`.

Activate your Python virtual environment.

```bash
source .env/bin/activate
```

## Install dependent Python packages

> Note: Python 3.6 or above is needed.

```bash
pip install nose
pip install demjson
```

## Local http server

Please read [README.md](./localhttpserver/README.md)

## Run tests

```bash
cd build/tools/
nosetests -v tests
```