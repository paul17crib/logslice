"""Timestamp parser for structured and unstructured log lines."""

import re
from datetime import datetime
from typing import Optional

# Common log timestamp patterns ordered by specificity
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:00.123Z or 2024-01-15T13:45:00+00:00
    (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))', '%Y-%m-%dT%H:%M:%S.%f'),
    # ISO 8601 without fractional seconds
    (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', '%Y-%m-%dT%H:%M:%S'),
    # Common log format: 2024-01-15 13:45:00,123
    (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', '%Y-%m-%d %H:%M:%S,%f'),
    # Common log format: 2024-01-15 13:45:00.123
    (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', '%Y-%m-%d %H:%M:%S.%f'),
    # Common log format: 2024-01-15 13:45:00
    (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
    # Syslog: Jan 15 13:45:00
    (r'([A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2})', '%b %d %H:%M:%S'),
    # Apache/nginx: 15/Jan/2024:13:45:00
    (r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})', '%d/%b/%Y:%H:%M:%S'),
]

_COMPILED_PATTERNS = [
    (re.compile(pattern), fmt) for pattern, fmt in TIMESTAMP_PATTERNS
]


def parse_timestamp(line: str) -> Optional[datetime]:
    """Extract and parse the first timestamp found in a log line.

    Args:
        line: A single log line string.

    Returns:
        A datetime object if a timestamp is found, otherwise None.
    """
    for regex, fmt in _COMPILED_PATTERNS:
        match = regex.search(line)
        if match:
            raw = match.group(1)
            # Normalize ISO 8601 with Z suffix
            raw_clean = raw.rstrip('Z').split('+')[0].split('-0')[0] if 'T' in raw else raw
            try:
                # Handle fractional seconds normalization
                if '.' in raw_clean:
                    dt = datetime.strptime(raw_clean[:26], fmt[:fmt.index('%f') + 2])
                else:
                    dt = datetime.strptime(raw_clean, fmt)
                return dt
            except ValueError:
                try:
                    dt = datetime.strptime(raw_clean, fmt.split('.')[0])
                    return dt
                except ValueError:
                    continue
    return None
