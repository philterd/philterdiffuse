# Philter Diffuse

Philter Diffuse provides mathematical guarantees for PII count aggregations using [OpenDP](https://github.com/opendp/opendp).

It uses the Discrete Laplace mechanism to privatize PII counts and generates compliance-ready reports with epsilon (privacy loss) interpretation. The tool also features persistent privacy budget tracking to prevent privacy loss exhaustion over time.

Designed to be used with [Phileas](https://www.github.com/philterd/phileas) and [Philter](https://www.github.com/philterd/philter).

## Key Features

- **Differential Privacy**: Implements the Discrete Laplace mechanism for robust privacy guarantees.
- **Privacy Budget Management**: Tracks epsilon spend across queries to prevent privacy leaks.
- **MongoDB Integration**: Directly fetch PII counts from MongoDB collections.
- **JSON Support**: Process PII counts from local JSON files.
- **Audit Reports**: Generates detailed compliance reports with privacy loss interpretation.
- **Thresholding**: Automatically hide low counts to further protect individual privacy.
