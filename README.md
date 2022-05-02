# Brane IDE

## Installation
To install the BraneScript and Bakery kernels for the Brane framework, you first have to install Docker in which the JupyterLab server will run.

To do so, you can follow any of the tutorials for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/), [Debian](https://docs.docker.com/engine/install/debian/), [Arch Linux](https://wiki.archlinux.org/title/docker) or [macOS](https://docs.docker.com/desktop/mac/install/).

Then, install the Docker [buildx]() plugin (you might already have done so when you installed Brane).

Once setup, you can then build the Docker image:
```bash
make brane-ide
```


## Running
Once installed, you can then launch the containerized JupyterLab environment:
```bash
make start-ide
```
This will launch a new JupyterLab instance that will connect to a Brane instance running at `127.0.0.1:50053`. Additionally, it will mount the `notebook` directory under `./notebook` (**important**, read below why this folder exists).

You may change these default properties by giving flags to the `make`-call:
- `BRANE_INSTANCE=<address>`: Attempts to connect to a Brane instance reachable by the given address. This address _should not_ contain `http://`, and should also include the port of the driver. For example, to connect to the standard port at the host `http://remote-host.com`:
  ```bash
  make start-ide BRANE_INSTANCE="remote-host.com:50053"
  ```
- `BRANE_NOTEBOOK_DIR=<dir>`: The persistent directory for notebook or other project files storage. Any data that you write to another folder is **removed when the container is removed as well.** Any relative path given is relative to the Makefile call, of course.  
  For example:
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

**Important**: Because the JupyterLab container is not persistent, everything you write will be discarded when you stop the container. To help with this, the Makefile will automatically mount the `notebooks` folder in the container to a persistent folder on disk. Please be aware that any important files should be placed under that folder!

If you moved files to/from the persistent folder, remember to hit the refresh button (the circle on top of the file list to the left) to be sure that JupyterLab updates its view of the folder.


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
