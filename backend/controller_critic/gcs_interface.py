# gcs_interface.py

# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"  <- do this before running the code in the shell

from google.cloud import storage
import json
import os
from typing import Dict, Any

class GCSContextManager:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def put_context(self, txn_id: str, data: Dict[str, Any]) -> None:
        blob = self.bucket.blob(f"contexts/{txn_id}.json")
        blob.upload_from_string(json.dumps(data), content_type='application/json')

    def get_context(self, txn_id: str) -> Dict[str, Any]:
        blob = self.bucket.blob(f"contexts/{txn_id}.json")
        if not blob.exists():
            return {}
        content = blob.download_as_text()
        return json.loads(content)
