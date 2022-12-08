# Brane IDE
Welcome to the repository about the Brane IDE in JupyterLab!

This repository contains the extensions and kernels necessary to connect to a Brane instance and run BraneScript or Bakery remotely.

> Unfortunately, the Bakery kernel is unsupported at the moment. The remainder of this README (and the rest of the repository) focusses on the BraneScript kernel only.


## Installation
To install the BraneScript and Bakery kernels for the Brane framework, you first have to install Docker in which the JupyterLab server will run.

To do so, you can follow any of the tutorials for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/), [Debian](https://docs.docker.com/engine/install/debian/), [Arch Linux](https://wiki.archlinux.org/title/docker) or [macOS](https://docs.docker.com/desktop/mac/install/).

Then, install the Docker [buildx](https://docs.docker.com/buildx/working-with-buildx/#install) plugin (you might already have done so when you installed Brane).

You will also have to have access to a Brane instance, and know where to find it (i.e., its IP-address). If you're testing with a local instance, make sure that you have deployed it (check [the documentation](https://wiki.enablingpersonalizedinterventions.nl/)).


## Running
Once installed, you can then launch the containerized JupyterLab environment:
```bash
make start-ide
```
This will launch a new JupyterLab instance that will connect to a Brane instance that is running locally. Additionally, it will mount the `notebook` directory under `./notebook` (**important**, read below why this folder exists).

If your instance is _not_ a local Docker deployment, you should change the endpoints where the notebook connects two using the following two options:
- `BRANE_DRV=<address>`: Changes the endpoint of the `brane-drv` service that will be used to execute workflows. It's similar to that used in `brane repl --remote` commands, except that this address should _not_ contain `http://`. For example, to connect to the standard `brane-drv` port at the host `http://remote-host.com`:
  ```bash
  make start-ide BRANE_DRV="remote-host.com:50053"
  ```

Usually, you'll need to supply both these options with the same address (but different prefix and port).

Aside from that, you can also change some other options using the CLI:
- `BRANE_NOTEBOOK_DIR=<dir>`: The persistent directory for notebook or other project files storage. You can think of this as 'changing the project directory'. Any data that you _don't_ write to this folder is **removed when the container is removed as well.**. Thus, to keep your notebooks around after you stopped the IDE, write them to the `notebooks` directory.
  For example, to mount a folder `awesome-brane-project`:
  ```bash
  make start-ide BRANE_NOTEBOOK_DIR="/home/user/awesome-brane-project"
  ```

Once launched, you may connect to the JupyterLab server by copying the address provided in the output of the command to your browser.

Then, you should select a 'BraneScript' kernel from the lab menu and use that to create a new BraneScript notebook.

To stop the server, run:
```bash
make stop-ide
```


## Usage
To use a BraneScript notebook, you can write one or more BraneScript lines in each cell. Then, hit 'run' (or `Ctrl+Enter`) to execute the given piece of code.

Note that all cells are executed in the same state; in other words, if you run the same cell twice, Brane will remember you doing so. This is most important for `import`-statements, as these can only be run once without any errors occurring.

**Important**: Because the JupyterLab container is not persistent, everything you write will be discarded when you stop the container. To help with this, the Makefile will automatically mounts the `notebooks` folder in the container to a persistent folder on disk. Please be aware that any important files should be placed under that folder!

If you moved files to/from the persistent folder from your OS, remember to hit the refresh button (the circle on top of the file list to the left) to be sure that JupyterLab updates its view of the folder.


### Showing images
To help with showing visual results of data pipelines, the JupyterLab kernel can show files that are 'printed' by BraneScript.

To show a file, run the following `print()`-command:
```
print("file:///data/<file>")
```
where `<file>` is the file to print. As you can see, this file has to live under the `data/` directory (which is also available from within Brane packages).

If that command is run, the JupyterLab kernel will replace that text with the contents of the file. It supports a couple of special extensions / MIME types:
- Files with the `.json` extension are interpreted as JSON and shown with foldeable regions and syntax highlighting.
- Files with the `.html` extension are interpreted as HTML and rendered as such.
- Files with MIME-type `image/*` are interpreted as images and shown as such.

Any other types are simple copied as raw text.


### Debugging
Currently, receiving debug messages from the Brane instance is not supported from within the JupyterLab environment. Instead, use the `brane` command-line tool to see debug messages instead.


## Contributing
Did you encounter a bug, issue or have a suggestion? Feel free to leave an issue at our [issues](https://github.com/epi-project/brane-ide) page!

Alternatively, create a pull request with the suggested change, and we'll take a look at it ASAP.
