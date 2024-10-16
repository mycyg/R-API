
# R Script Execution API with Docker and Flask

This repository provides a Flask API that allows users to execute R scripts with Docker. The API supports file inputs via URLs, executes R code, and returns the result as a downloadable file or image.

## Features

- **File Input via URL**: Users can submit file URLs (e.g., CSV files) for processing.
- **R Script Execution**: Users can send R code to be executed on the provided file.
- **Output as Downloadable File**: Generated images or other output files are returned as downloadable links.
- **Docker Integration**: The R script is executed inside a Docker container with all required dependencies pre-installed.

## Prerequisites

Ensure you have the following installed:

- **Docker**
- **Python 3**
- **Flask**

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/mycyg/R-API.git
    cd R-API
    ```

2. Create a Dockerfile and `run_r_script.sh` as described in this guide (they are also provided in this repository).

3. Build the Docker image:

    ```bash
    docker build -t r-script-runner .
    ```

4. Install the Python dependencies:

    ```bash
    pip install flask requests
    ```

## Usage

### Start the Flask Application

Run the following command to start the Flask API server:

```bash
python app.py
```

The API will be accessible at `http://127.0.0.1:5000`.

### API Request Structure

You can send a `POST` request to `http://127.0.0.1:5000/run-r` with the following parameters:

- `file_url`: URL to the file (e.g., a CSV file) to be processed by the R code.
- `code`: R code that processes the file. The R code can generate images, process data, and so on.

### Example Request

Here is an example using `curl`:

```bash
curl -X POST http://127.0.0.1:5000/run-r \
    -F 'file_url=http://example.com/data.csv' \
    -F 'code=library(readr); data <- read_csv("static/input_<unique_id>.csv"); print(data)'
```

### Example Response

- If the R code generates an image, the API will return a JSON response containing a download link:

    ```json
    {
        "download_link": "http://127.0.0.1:5000/static/output_<unique_id>.png"
    }
    ```

- If the R code generates text output, the response will contain the printed output of the R script:

    ```json
    {
        "output": "Printed output from the R script"
    }
    ```

## Project Structure

```
.
├── app.py                    # Flask API logic
├── Dockerfile                # Dockerfile to create the R environment
├── run_r_script.sh           # Shell script to run R code inside Docker
└── static/                   # Folder where output files will be stored
```

- **`app.py`**: Flask API logic that handles file downloads, R script execution, and returns the results.
- **`Dockerfile`**: Defines the R environment with necessary dependencies installed (e.g., `readr`, `ggplot2`).
- **`run_r_script.sh`**: Script that runs inside the Docker container to execute the provided R code.
- **`static/`**: Directory where generated files (e.g., images) are stored for download.

## How It Works

1. **File Input**: The user submits a URL that points to a file (e.g., a CSV file) and provides R code to process it.
2. **File Download**: The Flask server downloads the file from the provided URL.
3. **Docker Execution**: The R code and the downloaded file are passed to a Docker container, where the code is executed.
4. **Return Output**: If the R code generates an image or file, it is saved to the `static/` directory, and a download link is provided in the API response.

## Example Use Case

You can use this API to automate data analysis, generate reports, or visualize data using R. For example, a user could submit a CSV file link and R code that generates a plot. The API will return the plot as a downloadable image.

## Notes

- **Security Considerations**: Ensure that the API is properly secured when deployed in a production environment. R code execution can potentially be dangerous, so validation or sandboxing of code execution is recommended.
- **File Size**: Depending on the size of the file submitted, ensure that the server has enough storage space to handle large data files.

## License

This project is licensed under the MIT License.
```

