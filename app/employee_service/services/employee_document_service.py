from abc import ABC, abstractmethod
import math
import mimetypes
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...core.services.gcs_storage_service import GCS_STORAGE_SERVICE
from ..crud.crud_employee_document import CRUD_EMPLOYEE_DOCUMENT
from ..models.employee_document import EmployeeDocumentDb
from ..schemas.employee_document import (
    DocumentCategoryItem,
    EmployeeDocumentCreate,
    EmployeeDocumentDeleteResponse,
    EmployeeDocumentListResponse,
    EmployeeDocumentResponse,
    EmployeeDocumentUpdate,
)

SUPPORTED_CATEGORIES: Dict[str, Dict[str, str]] = {
    "govt_id_proof": {
        "label": "Government ID Proof",
        "description": "National ID, Aadhaar, Passport, PAN Card, Voter ID, or Driving License",
    },
    "profile_photo": {
        "label": "Profile Photo",
        "description": "Employee profile avatar / photograph",
    },
    "resume": {
        "label": "Resume / CV",
        "description": "Curriculum Vitae or Resume",
    },
    "contract": {
        "label": "Employment Contract / Offer",
        "description": "Offer Letter, Employment Agreement, NDA, or Appointment Letter",
    },
    "certificate": {
        "label": "Certificate / Degree",
        "description": "Educational Degree, Course Certificate, or Experience Letter",
    },
    "tax_document": {
        "label": "Tax / Financial Document",
        "description": "Tax Form, Form 16, Salary Slip, or Bank Statement",
    },
    "document": {
        "label": "General Document",
        "description": "Standard employee document or attachment",
    },
    "other": {
        "label": "Other",
        "description": "Other supporting documentation",
    },
}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB max file size


def _sanitize_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)[:100]
    safe_ext = re.sub(r"[^a-zA-Z0-9.]", "", ext)[:20].lower()
    return f"{safe_name}{safe_ext}" if safe_name else f"document{safe_ext}"


class IEmployeeDocumentService(ABC):
    @abstractmethod
    def upload(
        self,
        db: Session,
        *,
        employee_id: int,
        file: UploadFile,
        organization_id: Optional[uuid.UUID] = None,
        file_title: Optional[str] = None,
        file_category: str = "document",
        uploaded_by: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ) -> EmployeeDocumentResponse:
        pass

    @abstractmethod
    def get_by_id(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
        *,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentResponse:
        pass

    @abstractmethod
    def get_by_employee(
        self,
        db: Session,
        employee_id: int,
        *,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        search: Optional[str] = None,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentListResponse:
        pass

    @abstractmethod
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        employee_id: Optional[int] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentListResponse:
        pass

    @abstractmethod
    def update(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
        request: EmployeeDocumentUpdate,
    ) -> EmployeeDocumentResponse:
        pass

    @abstractmethod
    def delete(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
    ) -> EmployeeDocumentDeleteResponse:
        pass

    @abstractmethod
    def download_file(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
    ) -> Tuple[bytes, str, str]:
        pass

    @abstractmethod
    def get_categories(self) -> List[DocumentCategoryItem]:
        pass


class EmployeeDocumentService(IEmployeeDocumentService):
    def _enrich_response(
        self,
        db_obj: EmployeeDocumentDb,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentResponse:
        resp = EmployeeDocumentResponse.model_validate(db_obj)
        try:
            signed_url = GCS_STORAGE_SERVICE.generate_signed_url(
                blob_name=db_obj.gcs_blob_name,
                bucket_name=db_obj.gcs_bucket,
                expiration_minutes=signed_url_expiration_minutes,
            )
            resp.download_url = signed_url
        except Exception:
            resp.download_url = db_obj.file_url
        return resp

    def upload(
        self,
        db: Session,
        *,
        employee_id: int,
        file: UploadFile,
        organization_id: Optional[uuid.UUID] = None,
        file_title: Optional[str] = None,
        file_category: str = "document",
        uploaded_by: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ) -> EmployeeDocumentResponse:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a filename",
            )

        # Read file content
        try:
            file_bytes = file.file.read()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read uploaded file: {str(e)}",
            )

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file cannot be empty",
            )

        file_size = len(file_bytes)
        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {max_mb} MB",
            )

        # Sanitize filename & determine content type
        original_filename = file.filename
        safe_filename = _sanitize_filename(original_filename)
        _, ext = os.path.splitext(original_filename)
        file_extension = ext.lower() if ext else None

        content_type = file.content_type
        if not content_type or content_type == "application/octet-stream":
            guessed_type, _ = mimetypes.guess_type(original_filename)
            content_type = guessed_type or "application/octet-stream"

        # Validate category
        normalized_category = (file_category or "document").lower().strip()
        if normalized_category not in SUPPORTED_CATEGORIES:
            normalized_category = "document"

        target_bucket = bucket_name or GCS_STORAGE_SERVICE.default_bucket

        # Build GCS blob path: employees/{employee_id}/{category}/{unique_id}_{filename}
        unique_file_id = uuid.uuid4().hex[:12]
        gcs_blob_name = f"employees/{employee_id}/{normalized_category}/{unique_file_id}_{safe_filename}"

        # Upload to GCS / storage
        try:
            upload_result = GCS_STORAGE_SERVICE.upload_file(
                file_bytes=file_bytes,
                destination_blob_name=gcs_blob_name,
                content_type=content_type,
                bucket_name=target_bucket,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document to cloud storage: {str(e)}",
            )

        # Persist to database
        doc_create = EmployeeDocumentCreate(
            employee_id=employee_id,
            organization_id=organization_id,
            file_name=original_filename,
            file_title=file_title or original_filename,
            file_category=normalized_category,
            content_type=content_type,
            file_size=file_size,
            file_extension=file_extension,
            gcs_bucket=target_bucket,
            gcs_blob_name=gcs_blob_name,
            file_url=upload_result.get("media_link") or upload_result.get("public_url"),
            uploaded_by=uploaded_by,
            description=description,
        )

        db_obj = CRUD_EMPLOYEE_DOCUMENT.create(db, obj_in=doc_create)
        return self._enrich_response(db_obj)

    def get_by_id(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
        *,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentResponse:
        record = CRUD_EMPLOYEE_DOCUMENT.get(db, document_id=document_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee document not found with id '{document_id}'",
            )
        return self._enrich_response(record, signed_url_expiration_minutes)

    def get_by_employee(
        self,
        db: Session,
        employee_id: int,
        *,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        search: Optional[str] = None,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentListResponse:
        items = CRUD_EMPLOYEE_DOCUMENT.get_by_employee(
            db,
            employee_id=employee_id,
            skip=skip,
            limit=limit,
            category=category,
            search=search,
        )
        total = CRUD_EMPLOYEE_DOCUMENT.count_by_employee(
            db,
            employee_id=employee_id,
            category=category,
            search=search,
        )

        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1

        enriched_items = [
            self._enrich_response(item, signed_url_expiration_minutes)
            for item in items
        ]

        return EmployeeDocumentListResponse(
            items=enriched_items,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            employee_id=employee_id,
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        employee_id: Optional[int] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        signed_url_expiration_minutes: int = 60,
    ) -> EmployeeDocumentListResponse:
        items = CRUD_EMPLOYEE_DOCUMENT.get_multi(
            db,
            skip=skip,
            limit=limit,
            employee_id=employee_id,
            organization_id=organization_id,
            category=category,
            search=search,
        )
        total = CRUD_EMPLOYEE_DOCUMENT.count(
            db,
            employee_id=employee_id,
            organization_id=organization_id,
            category=category,
            search=search,
        )

        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1

        enriched_items = [
            self._enrich_response(item, signed_url_expiration_minutes)
            for item in items
        ]

        return EmployeeDocumentListResponse(
            items=enriched_items,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            employee_id=employee_id,
        )

    def update(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
        request: EmployeeDocumentUpdate,
    ) -> EmployeeDocumentResponse:
        record = CRUD_EMPLOYEE_DOCUMENT.get(db, document_id=document_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee document not found with id '{document_id}'",
            )
        updated = CRUD_EMPLOYEE_DOCUMENT.update(db, db_obj=record, obj_in=request)
        return self._enrich_response(updated)

    def delete(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
    ) -> EmployeeDocumentDeleteResponse:
        record = CRUD_EMPLOYEE_DOCUMENT.get(db, document_id=document_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee document not found with id '{document_id}'",
            )

        # Delete from GCS storage
        try:
            GCS_STORAGE_SERVICE.delete_file(
                blob_name=record.gcs_blob_name,
                bucket_name=record.gcs_bucket,
            )
        except Exception:
            # Continue even if already removed from storage
            pass

        CRUD_EMPLOYEE_DOCUMENT.remove(db, document_id=record.id)

        return EmployeeDocumentDeleteResponse(
            document_id=str(record.id),
            message="Employee document deleted successfully",
            success=True,
        )

    def download_file(
        self,
        db: Session,
        document_id: Union[uuid.UUID, str],
    ) -> Tuple[bytes, str, str]:
        record = CRUD_EMPLOYEE_DOCUMENT.get(db, document_id=document_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee document not found with id '{document_id}'",
            )

        try:
            file_bytes = GCS_STORAGE_SERVICE.download_file(
                blob_name=record.gcs_blob_name,
                bucket_name=record.gcs_bucket,
            )
            content_type = record.content_type or "application/octet-stream"
            return file_bytes, record.file_name, content_type
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to retrieve document content from storage: {str(e)}",
            )

    def get_categories(self) -> List[DocumentCategoryItem]:
        return [
            DocumentCategoryItem(
                id=cat_id,
                label=data["label"],
                description=data["description"],
            )
            for cat_id, data in SUPPORTED_CATEGORIES.items()
        ]


EMPLOYEE_DOCUMENT_SERVICE = EmployeeDocumentService()
