# Philter Diffuse

Philter Diffuse provides mathematical guarantees for PII count aggregations using OpenDP.

It uses the Discrete Laplace mechanism to privatize PII counts and generates compliance-ready reports with epsilon (privacy loss) interpretation. The tool also features persistent privacy budget tracking to prevent privacy loss exhaustion over time.

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

## Privacy Budget Management

Philter Diffuse tracks the total epsilon spent per collection (or JSON source) in a persistent metadata store:
- **MongoDB**: Stored in the `privacy_metadata` collection.
- **Local**: Stored in `privacy_budget.json` when using JSON files.

If the `--budget-ceiling` is reached, the tool will notify the user, apply infinite noise (effectively zeroing out or thresholding the results), and refuse to release further accurate information to protect privacy.

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Path to a JSON document containing PII entity counts. | None |
| `--mongo-uri` | MongoDB connection URI (format: `mongodb://host:port/database`). | `mongodb://localhost:27017/philter` |
| `--scale` | Scale for Laplace noise (higher = more privacy). | `2.0` |
| `--output` | Path to write the privatized PII counts to a CSV file. | **Required** |
| `--threshold` | Counts below this threshold will be output as `None`. | `0` |
| `--budget-ceiling` | The maximum total epsilon allowed per collection. | `10.0` |

## License

Copyright 2026 Philterd, LLC. "Philterd", "Phileas", and "Philter" are registered trademarks of Philterd, LLC.

This project is licensed under the Apache License, Version 2.0. See the `LICENSE` file for details.
