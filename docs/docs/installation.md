# Installation

Philter Diffuse can be installed directly as a Python package or run via Docker for convenience. 

## Prerequisites

Before installing Philter Diffuse, ensure your system meets the following requirements:

*   **Python**: Version 3.8 or higher is required.
*   **pip**: The standard Python package manager.
*   **MongoDB (Optional)**: If you plan to use MongoDB as a data source, ensure it's installed and accessible from your environment.
*   **Docker (Optional)**: If you prefer to run the application in a container.

## Direct Installation (Using pip)

1.  **Clone the Repository** (if applicable):
    ```bash
    git clone https://github.com/philterd/philterdiffuse.git
    cd philterdiffuse
    ```

2.  **Create a Virtual Environment** (Recommended):
    It's best practice to use a virtual environment to manage dependencies and avoid conflicts with other projects.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate     # On Windows
    ```

3.  **Install Dependencies**:
    The core dependencies for Philter Diffuse include `opendp`, `pymongo`, and other support libraries. Install them using the provided `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Docker Installation

Docker provides an isolated and consistent environment for running Philter Diffuse, eliminating potential "it works on my machine" issues.

### 1. Build the Docker Image

From the root of the project directory, build the image:

```bash
docker build -t philterdiffuse .
```

This will download the base Python image, copy the source code, and install all necessary dependencies inside the container.

### 2. Run the Container

You can run the container manually or use the provided `run-docker.sh` script, which automates common volume mounts for data processing.

**Example: Using the provided script**
```bash
./run-docker.sh
```

**Example: Running manually with volume mounts**
To process a local JSON file and save the output locally, mount your directories as volumes:
```bash
docker run -v $(pwd)/data:/data \
           philterdiffuse \
           --input /data/pii_counts.json \
           --output /data/privatized_counts.csv
```

## Verification

After installation, verify that Philter Diffuse is ready to use by running the help command:

```bash
python main.py --help
```

You should see a list of available command-line options and their descriptions.
