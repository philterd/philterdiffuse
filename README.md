# Philter Diffuse

Philter Diffuse provides mathematical guarantees for PII count aggregations using [OpenDP](https://github.com/opendp/opendp).

It uses the Discrete Laplace mechanism to privatize PII counts and generates compliance-ready reports with epsilon (privacy loss) interpretation. The tool also features persistent privacy budget tracking to prevent privacy loss exhaustion over time.

Designed to be used with [Phileas](https://www.github.com/philterd/phileas) and [Philter](https://www.github.com/philterd/philter).

View the documentation at https://philterd.github.io/philterdiffuse.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. **Option A: MongoDB**
   Ensure MongoDB is running and run:
   ```bash
   python main.py --mongo-uri "mongodb://localhost:27017/analytics_db" --output privatized_counts.csv
   ```

2. **Option B: JSON file**
   Provide a JSON document with PII entity counts:
   ```bash
   python main.py --input pii_counts.json --output privatized_counts.csv
   ```
   Sample `pii_counts.json`:
   ```json
   {
     "ssn": 10,
     "age": 45,
     "zipcode": 12,
     "creditcard": 5
   }
   ```

3. **Export to CSV**
   You can export privatized counts to a CSV file:
   ```bash
   python main.py --input pii_counts.json --output privatized_counts.csv
   ```

4. **Using Docker**
   You can also run the tool using Docker:
   ```bash
   ./run-docker.sh
   ```
   This script builds the image and runs a sample privatization task using volume mounts.

## Privacy Budget Management

Philter Diffuse tracks the total epsilon spent per collection (or JSON source) in a persistent metadata store. When using MongoDB, it is stored in the `privacy_metadata` collection. Otherwise, it is stored in a local file named `privacy_budget.json`.

If the `--budget-ceiling` is reached, the tool will notify the user, apply infinite noise (effectively zeroing out or thresholding the results), and refuse to release further accurate information to protect privacy.

## CLI Options

| Option | Description | Required? | Default |
|--------|-------------|-----------|---------|
| `--input` | Path to a JSON document containing PII entity counts. | Optional | None |
| `--mongo-uri` | MongoDB connection URI (format: `mongodb://host:port/database`). | Optional | `mongodb://localhost:27017/philter` |
| `--scale` | Scale for Laplace noise (higher = more privacy). | Optional | `2.0` |
| `--output` | Path to write the privatized PII counts to a CSV file. | **Required** | None |
| `--threshold` | Counts below this threshold will be output as `None`. | Optional | `0` |
| `--budget-ceiling` | The maximum total epsilon allowed per collection. | Optional | `10.0` |

## License

Copyright 2026 Philterd, LLC. "Philterd", "Phileas", and "Philter" are registered trademarks of Philterd, LLC.

This project is licensed under the Apache License, Version 2.0. See the `LICENSE` file for details.
