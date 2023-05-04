# PROBoter web UI

The unified PROBoter web frontend created with [Vue.js](https://vuejs.org/).

## Preconditions (NodeJS setup)

For development of the Web UI code, a [node.js](https://nodejs.org/en/) installation is
required. All additional dependencies are defined by the project. Therefore,
a working development setup can be created with the following commands:

```
sudo apt update
sudo apt install node
```

In case of Debian unstable, use:

```
curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
apt-get install -y nodejs
```

Finally, run

```
npm install
```

## Setup

Because developers are always in a rush, the project contains a `Makefile` to
automate most common tasks. To get an overview of the available make targets
just run `make` in the project directory:

```
 ~/ make

start                          Start the development server
lint                           Linting and type checking
format                         Code formatting
image-build                    Build the image
image-build-nc                 Build the image without caching
image-remove-force             Remove the latest image (forced)
container-run                  Run container (with X-forwarding)
container-stop                 Stop a running container
container-remove               Remove a (running) container
container-restart              Restart the container
help                           This help
```

The `lint`, `format` targets are designed to check and format the code.

For an interactive development experience, you can use the `start` target to
start the [Vite](https://vitejs.dev/) development server with hot reloading
activated. The started server listens by default only on the local loop-back
interface on port `3000`.

During development is recommended to start at least the [project storage](../project-storage/)
microservice. In addition, the [hardware control](../hardware-control/) microservice can be
started in `simulation mode`.

The recommended way to use the hardware control service in a production is
to package it as a [Docker](https://www.docker.com/) image. Use the `image-xxx`
targets to build the Docker image. To create and start a container based on the
generated Docker image you can use the `container-xxx` targets.

## License

The PROBoter web UI is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt).

## Credits

The service depends on functionality from the following third-party packages:

- [axios](https://axios-http.com/)
- [Bootstrap](https://getbootstrap.com/)
- [buffer](https://github.com/feross/buffer)
- [Vue.js](https://vuejs.org/)
- [Three.js](https://threejs.org/)
- [Mitt](https://github.com/developit/mitt)
- [tween.js](https://github.com/tweenjs/tween.js/)
- [Popper](https://github.com/floating-ui/floating-ui)
- [FileSaver.js](https://github.com/eligrey/FileSaver.js)
- [vuejs-logger](https://github.com/justinkames/vuejs-logger)

We like to thank the package authors for their great work and effort!
