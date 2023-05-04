# Reverse proxy

Reverse proxy setup based on [nginx](https://nginx.org/) to expose all PROBoter-related
(mircor)services over a single port.

## Setup

Because developers are always in a rush, the project contains a `Makefile` to
automate most common tasks. To get an overview of the available make targets
just run `make` in the project directory

```
 ~/ make

start                          Start with development config
help                           This help
```

The `start` target starts a Docker container based on the latest [nginx image](https://hub.docker.com/_/nginx).
In this setup, incoming requests are redirected to PROBoter services started in development mode and
listening on the loopback interface (usually by executing `make start` in the respective
microservice sub-folders).

## License

The reverse proxy service is licensed under the 
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt).

## Credits

The service depends on functionality from the following third-party tools:

- [nginx](https://nginx.org/) 

We like to thank the tool authors for their great work and effort!

