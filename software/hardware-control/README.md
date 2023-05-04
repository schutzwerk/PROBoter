# PROBoter hardware control service

A core service in the PROBoter software architecture to control the hardware
platform. It provides the following main features via a REST-like interface:

- Configuration of the PROBoter hardware platform
- Low-level interaction with the PROBOter hardware platform like calibration or direct probe movement
- High-level functionality like PCB scanning or probing
- Websocket-based event notifications to connected clients

## Setup

Because developers are always in a rush, the project contains a `Makefile` to
automate most common tasks. To get an overview of the available make targets
just run `make` in the project directory:

```
 ~/ make

init                           Local dev. setup initialization
lint                           Source code linting
format                         Source code formatting according to PEP8
unit-test                      Run unit tests
coverage                       Run unit tests with code coverage
start                          Start the hardware control server (simulated hardware)
start-simulation               Start the hardware control server (real hardware)
init-db                        Seed the database with dummy data
image-build                    Build the image
image-build-nc                 Build the image without caching
image-remove-force             Remove the latest image (forced)
container-run                  Run container
container-stop                 Stop a running container
container-remove               Remove a (running) container
container-restart              Restart the container
help                           This help
```

The `init` target basically sets up a local development environment based on
[Pipenv](https://pypi.org/project/pipenv/). You can do the same by running the
following commands in your terminal:

```
pipenv install --dev pylint pytest coverage autopep8 schema rope pytest-asyncio && \
pipenv install libs/mtracker-0.0.1-py3-none-any.whl && \
pipenv install -e .
```

The `lint`, `format`, `unit-test` and `coverage` targets are designed to check
and format the code.

For an interactive development experience, you can use the `start` target to
start the [Quart](https://github.com/pallets/quart/) development server with
hot reloading activated. The started server listens by default only on the
local loop-back interface on port `5003`.

The recommended way to use the hardware control service in a production is
to package it as a [Docker](https://www.docker.com/) image. Use the `image-xxx`
targets to build the Docker image. To create and start a container based on the
generated Docker image you can use the `container-xxx` targets.

## License

The PCB analysis service is licensed under the [GNU General Public License
v3.0](https://www.gnu.org/licenses/gpl-3.0.txt).

## Credits

The service depends on functionality from the following third-party packages:

- [aiohttp](https://github.com/aio-libs/aiohttp)
- [quart](https://github.com/pallets/quart/)
- [quart-schema](https://github.com/pgjones/quart-schema)
- [quart-cors](https://github.com/pgjones/quart-cors/)
- [tortoise-orm](https://github.com/tortoise/tortoise-orm)
- [pydantic](https://github.com/pydantic/pydantic)
- [pyudev](https://github.com/pyudev/pyudev)
- [pyserial](https://github.com/pyserial/pyserial)
- [pyserial-asyncio](https://github.com/pyserial/pyserial-asyncio)
- [scipy](https://github.com/scipy/scipy)
- [numpy](https://github.com/numpy/numpy)
- [disjoint-set](https://github.com/mrapacz/disjoint-set)
- [OpenCV](https://opencv.org/)

We like to thank the package authors for their great work and effort!
