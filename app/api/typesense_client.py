# app/api/typesense_client.py
import os
import typesense

TYPESENSE_KEY  = os.getenv("TYPESENSE_API_KEY", "xyz123")
TYPESENSE_HOST = os.getenv("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT = os.getenv("TYPESENSE_PORT", "8108")

ts_client = typesense.Client({
    "nodes": [{
        "host": TYPESENSE_HOST,
        "port": TYPESENSE_PORT,
        "protocol": "http"
    }],
    "api_key": TYPESENSE_KEY,
    "connection_timeout_seconds": 2
})
