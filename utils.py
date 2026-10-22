import hashlib
from datetime import datetime


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def parse_datetime(date_text, time_text):
    return datetime.strptime(
        f"{date_text} {time_text}",
        "%Y-%m-%d %H:%M"
    )


def valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def valid_time(time_text):
    try:
        datetime.strptime(time_text, "%H:%M")
        return True
    except ValueError:
        return False