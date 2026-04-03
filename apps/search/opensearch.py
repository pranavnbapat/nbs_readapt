from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from opensearchpy import OpenSearch


def get_opensearch_client() -> OpenSearch:
    config = settings.OPENSEARCH
    parsed = urlparse(config["url"])
    use_ssl = parsed.scheme == "https"

    client_kwargs = {
        "hosts": [
            {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or (443 if use_ssl else 80),
            }
        ],
        "use_ssl": use_ssl,
        "verify_certs": use_ssl,
    }

    username = config.get("username") or ""
    password = config.get("password") or ""
    if username and password:
        client_kwargs["http_auth"] = (username, password)

    return OpenSearch(**client_kwargs)
