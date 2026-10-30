from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Protocol


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def checked_key(key: str) -> str:
    if (
        not key
        or key.startswith("/")
        or "\\" in key
        or any(p in ("", ".", "..") for p in key.split("/"))
    ):
        raise ValueError(f"Invalid storage key: {key}")
    return key


class Store(Protocol):
    def put(self, key: str, data: bytes, content_type: str): ...
    def read_json(self, key: str) -> dict | None: ...
    def exists(self, key: str) -> bool: ...
    def delete(self, key: str): ...
    def object_key(self, key: str) -> str: ...


class LocalStore:
    bucket = None

    def __init__(self, root: Path):
        self.root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / checked_key(key)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Storage path escapes root")
        return path

    def put(self, key: str, data: bytes, content_type: str):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temp = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
        finally:
            if temp:
                temp.unlink(missing_ok=True)

    def read_json(self, key: str) -> dict | None:
        try:
            return json.loads(self._path(key).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def delete(self, key: str):
        self._path(key).unlink(missing_ok=True)

    def object_key(self, key: str) -> str:
        return checked_key(key)


class S3Store:
    """Uses the normal AWS credential chain (e.g. an EC2 instance role)."""

    def __init__(self, bucket: str, prefix: str = "legislation", client=None):
        if client is None:
            import boto3

            client = boto3.client("s3")
        self.client, self.bucket = client, bucket
        self.prefix = checked_key(prefix.strip("/")) if prefix.strip("/") else ""

    def _key(self, key):
        return str(PurePosixPath(self.prefix) / checked_key(key))

    def put(self, key: str, data: bytes, content_type: str):
        self.client.put_object(
            Bucket=self.bucket, Key=self._key(key), Body=data, ContentType=content_type
        )

    def read_json(self, key: str) -> dict | None:
        from botocore.exceptions import ClientError

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
            with response["Body"] as body:
                return json.loads(body.read().decode("utf-8"))
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "404", "NotFound"):
                return None
            raise

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(key))
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "404", "NotFound"):
                return False
            raise

    def delete(self, key: str):
        self.client.delete_object(Bucket=self.bucket, Key=self._key(key))

    def object_key(self, key: str) -> str:
        return self._key(key)
