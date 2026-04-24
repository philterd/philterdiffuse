# Usage

Philter Diffuse can be used with either a MongoDB instance or a local JSON file containing PII counts.

## Command Line Interface

The primary way to interact with Philter Diffuse is through the CLI.

### Option A: MongoDB

If you have PII counts stored in a MongoDB collection, you can fetch them directly:

```bash
python main.py --mongo-uri "mongodb://localhost:27017/analytics_db" --output privatized_counts.csv
```

By default, it monitors fields: `creditcard`, `ssn`, `age`, and `zipcode`.

### Option B: JSON file

You can provide a JSON document with PII entity counts:

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

## CLI Options

| Option | Description | Required? | Default |
|--------|-------------|-----------|---------|
| `--input` | Path to a JSON document containing PII entity counts. | Optional | None |
| `--mongo-uri` | MongoDB connection URI (format: `mongodb://host:port/database`). | Optional | `mongodb://localhost:27017/philter` |
| `--scale` | Scale for Laplace noise (higher = more privacy, less accuracy). | Optional | `2.0` |
| `--output` | Path to write the privatized PII counts to a CSV file. | **Required** | None |
| `--threshold` | Counts below this threshold will be output as `None`. | Optional | `0` |
| `--budget-ceiling` | The maximum total epsilon allowed per collection. | Optional | `10.0` |

## Audit Reports

After each execution, Philter Diffuse generates a compliance-ready report in the console. This report includes:

- **Privacy Loss (Epsilon)**: The amount of privacy budget consumed by this query.
- **Protection Strength**: A qualitative interpretation of the epsilon value (e.g., EXTREME, HIGH, MODERATE, LOW).
- **Influence Limit**: The maximum mathematical influence any single individual can have on the results.
- **Raw vs. Private Counts**: A comparison of the original and privatized counts (for internal auditing).
