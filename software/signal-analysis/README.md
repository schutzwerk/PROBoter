# Voltage measurement analysis server

A simple web server that identifies the original functionality of voltage
signal data.

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
start                          Start the PCB analysis server
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
pipenv --three
pipenv install --dev pylint pytest coverage autopep8 schema rope matplotlib
pipenv install -e .
```

The `lint`, `format`, `unit-test` and `coverage` targets are designed to check
and format the code.

For an interactive development experience, you can use the `start` target to
start a [werkzeug](https://werkzeug.palletsprojects.com/en/2.1.x/) development
server with hot reloading activated. The started server listens by default only
on the local loop-back interface on port `5002`.

The recommended way to use the voltage signal analysis service in a production is
to package it as a [Docker](https://www.docker.com/) image. Use the `image-xxx`
targets to build the Docker image. To create and start a container based on the
generated Docker image you can use the `container-xxx` targets.

## How to use

The analysis functionality is provided via a REST-like interface which is
documented with [Swagger](https://swagger.io/). You can find the API
documentation with a nice graphical interface provided by
[SwaggerUI](https://swagger.io/tools/swagger-ui/) at <http://localhost:5002/api/v1>.

## License

The signal analysis service is licensed under the [GNU General Public License
v3.0](https://www.gnu.org/licenses/gpl-3.0.txt).

## Credits

The service depends on functionality from the following third-party packages:

- [flask](https://github.com/pallets/flask)
- [flask-cors](https://github.com/corydolphin/flask-cors)
- [flask-restx](https://github.com/python-restx/flask-restx)
- [matplotlib](https://github.com/matplotlib/matplotlib)
- [scipy](https://github.com/scipy/scipy)
- [scikit-commpy](https://github.com/veeresht/CommPy)

We like to thank the package authors for their great work and effort!

