from datetime import datetime, timezone


def parse_datetime(datetime_str: str):
    """
    Parse datetime string with various formats.
    """

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S+00:00",
        "%Y-%m-%d %H:%M:%S+00",
        "%Y-%m-%d %H:%M:%SZ",
        "%Y-%m-%d %H:%M:%SZ+00:00",
        "%Y-%m-%d %H:%M:%SZ+00",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f+00:00",
        "%Y-%m-%d %H:%M:%S.%f+00",
        "%Y-%m-%d %H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S.%fZ+00:00",
        "%Y-%m-%d %H:%M:%S.%fZ+00",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S+00:00",
        "%Y-%m-%dT%H:%M:%S+00",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%SZ+00:00",
        "%Y-%m-%dT%H:%M:%SZ+00",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f+00:00",
        "%Y-%m-%dT%H:%M:%S.%f+00",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%fZ+00:00",
        "%Y-%m-%dT%H:%M:%S.%fZ+00",
        "%Y-%m-%d",
    ]

    for format_string in formats:
        try:
            dt = datetime.strptime(datetime_str, format_string)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise ValueError("Timestamp does not match any of the expected formats", datetime_str)
