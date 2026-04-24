# Installation

To install Philter Diffuse, you need Python installed on your system.

## Using pip

You can install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

## Using Docker

Alternatively, you can run Philter Diffuse using Docker. This ensures a consistent environment and simplifies dependency management.

1. **Build the Docker image:**

   ```bash
   docker build -t philterdiffuse .
   ```

2. **Run the container:**

   You can use the provided `run-docker.sh` script as a template:

   ```bash
   ./run-docker.sh
   ```

   The script builds the image and runs a sample privatization task using volume mounts for input and output.
