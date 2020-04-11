from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path
from pytz import timezone
import random
import string
from tzlocal import get_localzone
import yaml

# Helpers must:
# - stand alone: do not import other parts of the opp library
# - contain no free variables: all variables are bound in the function head
# - not mutate their inputs


def random_text(n):
    """
    Produce a random string of letters and numbers

    Args:
        n - length of the string

    Return:
        a string of ascii letters and numbers
    """
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(n))


def load_settings():
    """Initialize settings"""
    database_uri = os.environ.get("OPP_DATABASE", None)

    if database_uri is None:
        raise ValueError("OPP_DATABASE must be set as environmental variable")

    base_pathname = os.environ.get(
        "OPP_DIR", "/usr/local/share/one_page_podcast")
    base_path = Path(base_pathname)
    tz_string = os.environ.get("OPP_TIMEZONE")

    if tz_string is None:
        tz = get_localzone()
    else:
        tz = timezone(tz_string)

    config = {
        "database_uri": database_uri,
        "path": {
            "media": base_path / "media",
            "static": base_path / "static",
            "template": base_path / "template"
            },
        "timezone": tz
    }

    loc = os.environ.get("OPP_CONFIG", "/etc/one_page_podcast.yml")
    path = Path(loc)

    with path.open() as f:
        podcast = yaml.safe_load(f.read())

    return {"config": config, "podcast": podcast}


class Auth:
    """Handle administrator login."""

    def __init__(self):
        """Initialize."""
        username = os.environ.get("OPP_USER")

        if username is None:
            raise ValueError("OPP_USER environmental variable must be configured.")

        password = os.environ.get("OPP_PASS")

        if password is None:
            raise ValueError("OPP_PASS environmental variable must be configured.")

        # This is probably overkill considering it's already all in-memory.
        self._salt = os.urandom(32)
        combo = username + password
        self._key = hashlib.pbkdf2_hmac(
            "sha256", combo.encode("utf-8"), self._salt, 100000, dklen=128)

    def valid(self, username, password):
        """Validate a login"""
        combo = username + password
        check = hashlib.pbkdf2_hmac(
            "sha256", combo.encode("utf-8"), self._salt, 100000, dklen=128)

        return check == self._key
