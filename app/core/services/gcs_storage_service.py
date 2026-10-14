import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "hrms-aaralia")
LOCAL_UPLOADS_DIR = Path("uploads")


class GCSStorageService:
    """
    Google Cloud Storage Service managing uploads and retrieval
    for the 'hrms-aaralia' bucket with seamless local-development fallback.
    """

    def __init__(self, bucket_name: str = DEFAULT_BUCKET_NAME):
        self.bucket_name = bucket_name
        self.client = None
        self.is_gcs_available = False
        self._init_gcs_client()

    @property
    def default_bucket(self) -> str:
        return self.bucket_name

    def _init_gcs_client(self):
        try:
            from google.cloud import storage

            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")

            if cred_path and os.path.exists(cred_path):
                self.client = storage.Client.from_service_account_json(cred_path, project=project_id)
            elif project_id:
                self.client = storage.Client(project=project_id)
            else:
                self.client = storage.Client()

            # Verify client connectivity or credentials
            self.is_gcs_available = True
            logger.info(f"Google Cloud Storage initialized successfully for bucket '{self.bucket_name}'")
        except Exception as e:
            self.client = None
            self.is_gcs_available = False
            LOCAL_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            logger.warning(
                f"Google Cloud Storage client not active (using local storage fallback in '{LOCAL_UPLOADS_DIR}'): {e}"
            )

    def upload_file(
        self,
        file_bytes: bytes,
        destination_blob_name: str,
        content_type: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Uploads file content to the specified destination blob in GCS (or local fallback).
        """
        target_bucket = bucket_name or self.bucket_name
        sanitized_blob = destination_blob_name.lstrip("/").replace("\\", "/")

        if self.is_gcs_available and self.client:
            try:
                bucket = self.client.bucket(target_bucket)
                blob = bucket.blob(sanitized_blob)

                blob.upload_from_string(
                    file_bytes,
                    content_type=content_type or "application/octet-stream",
                )

                public_url = f"https://storage.googleapis.com/{target_bucket}/{sanitized_blob}"

                return {
                    "bucket": target_bucket,
                    "blob_name": sanitized_blob,
                    "content_type": content_type or "application/octet-stream",
                    "file_size": len(file_bytes),
                    "file_url": public_url,
                    "storage_provider": "gcs",
                }
            except Exception as e:
                logger.error(f"GCS upload failed for '{sanitized_blob}': {e}. Falling back to local storage.")

        # Local filesystem fallback
        local_path = LOCAL_UPLOADS_DIR / sanitized_blob
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_bytes)

        fallback_url = f"/api/v1/employee-documents/raw/{sanitized_blob}"
        return {
            "bucket": target_bucket,
            "blob_name": sanitized_blob,
            "content_type": content_type or "application/octet-stream",
            "file_size": len(file_bytes),
            "file_url": fallback_url,
            "storage_provider": "local",
        }

    def generate_signed_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60,
        bucket_name: Optional[str] = None,
    ) -> str:
        """
        Generates a temporary signed URL for secure, direct file viewing/downloading.
        """
        target_bucket = bucket_name or self.bucket_name
        sanitized_blob = blob_name.lstrip("/").replace("\\", "/")

        if self.is_gcs_available and self.client:
            try:
                bucket = self.client.bucket(target_bucket)
                blob = bucket.blob(sanitized_blob)
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(minutes=expiration_minutes),
                    method="GET",
                )
                return signed_url
            except Exception as e:
                logger.warning(f"Could not generate signed URL for '{sanitized_blob}': {e}")

        # Return standard public URL or internal endpoint URL
        return f"https://storage.googleapis.com/{target_bucket}/{sanitized_blob}"

    def download_file(
        self,
        blob_name: str,
        bucket_name: Optional[str] = None,
    ) -> bytes:
        """
        Downloads the file bytes directly from GCS or local fallback.
        """
        target_bucket = bucket_name or self.bucket_name
        sanitized_blob = blob_name.lstrip("/").replace("\\", "/")

        if self.is_gcs_available and self.client:
            try:
                bucket = self.client.bucket(target_bucket)
                blob = bucket.blob(sanitized_blob)
                return blob.download_as_bytes()
            except Exception as e:
                logger.error(f"Failed to download from GCS '{sanitized_blob}': {e}")

        # Check local fallback
        local_path = LOCAL_UPLOADS_DIR / sanitized_blob
        if local_path.exists():
            with open(local_path, "rb") as f:
                return f.read()

        raise FileNotFoundError(f"File '{sanitized_blob}' not found in GCS bucket '{target_bucket}' or local storage")

    def delete_file(
        self,
        blob_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """
        Deletes the file from GCS or local fallback storage.
        """
        target_bucket = bucket_name or self.bucket_name
        sanitized_blob = blob_name.lstrip("/").replace("\\", "/")
        deleted = False

        if self.is_gcs_available and self.client:
            try:
                bucket = self.client.bucket(target_bucket)
                blob = bucket.blob(sanitized_blob)
                if blob.exists():
                    blob.delete()
                    deleted = True
            except Exception as e:
                logger.error(f"Failed to delete blob '{sanitized_blob}' from GCS: {e}")

        local_path = LOCAL_UPLOADS_DIR / sanitized_blob
        if local_path.exists():
            try:
                local_path.unlink()
                deleted = True
            except Exception as e:
                logger.warning(f"Failed to delete local fallback file '{local_path}': {e}")

        return deleted

    def file_exists(
        self,
        blob_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Checks if a file exists in GCS or local fallback storage."""
        target_bucket = bucket_name or self.bucket_name
        sanitized_blob = blob_name.lstrip("/").replace("\\", "/")

        if self.is_gcs_available and self.client:
            try:
                bucket = self.client.bucket(target_bucket)
                blob = bucket.blob(sanitized_blob)
                return blob.exists()
            except Exception:
                pass

        local_path = LOCAL_UPLOADS_DIR / sanitized_blob
        return local_path.exists()


GCS_STORAGE_SERVICE = GCSStorageService()
