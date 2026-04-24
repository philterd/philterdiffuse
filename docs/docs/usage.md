# Usage

Philter Diffuse is a command-line tool designed to process PII counts and apply differential privacy. It supports two primary modes of operation: fetching data from a MongoDB database or processing a local JSON file.

## Input Modes

### 1. MongoDB Mode (Default)

In this mode, Philter Diffuse connects to a MongoDB instance, queries specified collections for PII entity occurrences, and privatizes the resulting counts.

**Example Command:**
```bash
python main.py --mongo-uri "mongodb://localhost:27017/analytics_db" --output results.csv
```

*   **Behavior**: It connects to the `analytics_db` on `localhost`.
*   **Monitored Fields**: By default, the tool counts occurrences of the following fields in the database: `creditcard`, `ssn`, `age`, and `zipcode`.

### 2. JSON Mode

If you already have a JSON file containing the counts of various PII types, you can provide it directly using the `--input` flag. This is ideal for integration with existing logging or data pipeline tools.

**Example Command:**
```bash
python main.py --input data/pii_counts.json --output results.csv
```

**Expected JSON Format:**
The JSON file should be a simple flat object where keys represent the PII type and values are the integer counts.
```json
{
  "ssn": 105,
  "age": 450,
  "zipcode": 122,
  "creditcard": 58,
  "email": 210
}
```

## Command Line Options

| Option | Long Flag | Description | Default |
| :--- | :--- | :--- | :--- |
| `-i` | `--input` | Path to a local JSON file containing PII counts. If omitted, MongoDB mode is used. | `None` |
| `-m` | `--mongo-uri` | The connection string for your MongoDB instance. | `mongodb://localhost:27017/philter` |
| `-s` | `--scale` | The **scale** parameter for the Laplace noise. A higher scale adds more noise (more privacy, less accuracy). | `2.0` |
| `-o` | `--output` | **[Required]** The file path where the privatized CSV results will be saved. | `None` |
| `-t` | `--threshold` | Results with a privatized count below this value will be masked as `None` in the output. | `0` |
| `-b` | `--budget-ceiling` | The maximum cumulative privacy budget (epsilon) allowed for a single source. | `10.0` |

---

## Output Formats

Philter Diffuse provides two forms of output for every execution:

### 1. Privatized CSV File
The file specified by the `--output` flag will contain a list of PII types and their corresponding privatized counts.

**Example CSV Content:**
```csv
PII Type,Private Count
ssn,107
age,448
zipcode,125
creditcard,None
```
*Note: `creditcard` is "None" because its privatized count fell below the configured threshold.*

### 2. Privacy Audit Report
A human-readable report is printed to the standard output (`stdout`) summarizing the execution and the privacy guarantees applied.

**Key Report Sections:**
*   **Privacy Loss (Epsilon)**: The specific amount of privacy budget consumed by this particular execution (calculated as `1 / scale`).
*   **Protection Strength**: A qualitative assessment of the privacy level (e.g., "HIGH" or "MODERATE").
*   **Influence Limit**: A mathematical multiplier representing the maximum change an individual record can have on the output probability.
*   **Raw vs. Private Table**: A side-by-side comparison for internal auditing (only visible to the user running the tool).

## Practical Example: Increasing Privacy

If you are dealing with extremely sensitive data and want to increase the privacy protection, increase the `--scale` parameter:

```bash
python main.py --input pii_counts.json --output private.csv --scale 5.0 --threshold 10
```

In this example:
1.  **Scale 5.0**: Adds significantly more noise than the default (2.0), resulting in a lower epsilon (0.2).
2.  **Threshold 10**: Any PII count that, after adding noise, is less than 10 will be completely masked as `None`.
