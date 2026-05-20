# logslice

Fast log file slicer that extracts time-range segments from large structured or unstructured log files.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Extract logs between two timestamps
logslice --input app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00"

# Save output to a file
logslice --input app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --output slice.log

# Specify a custom timestamp format
logslice --input app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --fmt "%Y-%m-%d %H:%M:%S"
```

You can also use logslice as a Python library:

```python
from logslice import slice_log

slice_log(
    input_path="app.log",
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00",
    output_path="slice.log"
)
```

---

## Features

- Handles large log files efficiently using binary search
- Supports structured and unstructured log formats
- Customizable timestamp patterns via regex or `strptime` format strings
- Works as a CLI tool or importable Python module

---

## License

This project is licensed under the [MIT License](LICENSE).