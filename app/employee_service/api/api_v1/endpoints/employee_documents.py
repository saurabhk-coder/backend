import uuid
from typing import List, Optional
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    Path,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from ....schemas.employee_document import (
    DocumentCategoryItem,
    EmployeeDocumentDeleteResponse,
    EmployeeDocumentListResponse,
    EmployeeDocumentResponse,
    EmployeeDocumentUpdate,
)
from ....services.employee_document_service import (
    EMPLOYEE_DOCUMENT_SERVICE,
)
from ...deps import get_db

employee_documents_router = APIRouter()


@employee_documents_router.get(
    "/employee-documents/categories",
    response_model=List[DocumentCategoryItem],
    summary="Get supported document categories",
    description="Returns a list of supported document categories (e.g. govt_id_proof, profile_photo, resume, contract, certificate, tax_document, other).",
)
def get_document_categories() -> List[DocumentCategoryItem]:
    return EMPLOYEE_DOCUMENT_SERVICE.get_categories()


@employee_documents_router.post(
    "/employees/{employee_id}/documents/upload",
    response_model=EmployeeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document for a specific employee",
    description="Uploads a file directly to Google Cloud Storage bucket (hrms-aaralia) and stores document metadata linked to the employee.",
)
def upload_employee_document(
    employee_id: int = Path(..., description="ID of the employee"),
    file: UploadFile = File(..., description="File to upload"),
    file_title: Optional[str] = Form(None, description="Display title for the document"),
    file_category: str = Form(
        "document",
        description="Category (govt_id_proof, profile_photo, resume, contract, certificate, tax_document, other)",
    ),
    organization_id: Optional[uuid.UUID] = Form(None, description="Organization ID"),
    uploaded_by: Optional[uuid.UUID] = Form(None, description="User ID of uploader"),
    description: Optional[str] = Form(None, description="Optional description/notes"),
    db: Session = Depends(get_db),
) -> EmployeeDocumentResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.upload(
        db=db,
        employee_id=employee_id,
        file=file,
        organization_id=organization_id,
        file_title=file_title,
        file_category=file_category,
        uploaded_by=uploaded_by,
        description=description,
    )


@employee_documents_router.post(
    "/employee-documents/upload",
    response_model=EmployeeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="General document upload endpoint",
    description="Uploads a file to Google Cloud Storage bucket (hrms-aaralia) with employee_id passed in form-data.",
)
def upload_document_general(
    employee_id: int = Form(..., description="ID of the employee"),
    file: UploadFile = File(..., description="File to upload"),
    file_title: Optional[str] = Form(None, description="Display title for the document"),
    file_category: str = Form(
        "document",
        description="Category (govt_id_proof, profile_photo, resume, contract, certificate, tax_document, other)",
    ),
    organization_id: Optional[uuid.UUID] = Form(None, description="Organization ID"),
    uploaded_by: Optional[uuid.UUID] = Form(None, description="User ID of uploader"),
    description: Optional[str] = Form(None, description="Optional description/notes"),
    db: Session = Depends(get_db),
) -> EmployeeDocumentResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.upload(
        db=db,
        employee_id=employee_id,
        file=file,
        organization_id=organization_id,
        file_title=file_title,
        file_category=file_category,
        uploaded_by=uploaded_by,
        description=description,
    )


@employee_documents_router.get(
    "/employees/{employee_id}/documents",
    response_model=EmployeeDocumentListResponse,
    summary="List all uploaded documents for an employee",
    description="Allows employees or HR administrators to see all uploaded files for an employee with direct/signed download URLs.",
)
def get_employee_documents(
    employee_id: int = Path(..., description="Employee ID"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. govt_id_proof, resume)"),
    search: Optional[str] = Query(None, description="Search by file name or title"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    signed_url_expiration_minutes: int = Query(60, ge=1, le=1440, description="Validity period of signed URLs in minutes"),
    db: Session = Depends(get_db),
) -> EmployeeDocumentListResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.get_by_employee(
        db=db,
        employee_id=employee_id,
        skip=skip,
        limit=limit,
        category=category,
        search=search,
        signed_url_expiration_minutes=signed_url_expiration_minutes,
    )


@employee_documents_router.get(
    "/employee-documents",
    response_model=EmployeeDocumentListResponse,
    summary="List employee documents with optional filters",
    description="Retrieve paginated documents across employees with filters by employee_id, organization_id, category, and search text.",
)
def list_employee_documents(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    organization_id: Optional[uuid.UUID] = Query(None, description="Filter by organization ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by filename or title"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    signed_url_expiration_minutes: int = Query(60, ge=1, le=1440, description="Signed URL validity in minutes"),
    db: Session = Depends(get_db),
) -> EmployeeDocumentListResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        organization_id=organization_id,
        category=category,
        search=search,
        signed_url_expiration_minutes=signed_url_expiration_minutes,
    )


@employee_documents_router.get(
    "/employee-documents/{document_id}",
    response_model=EmployeeDocumentResponse,
    summary="Get document details by document ID",
    description="Fetches document metadata along with a fresh signed download URL.",
)
def get_employee_document(
    document_id: uuid.UUID = Path(..., description="Document unique identifier"),
    signed_url_expiration_minutes: int = Query(60, ge=1, le=1440, description="Signed URL expiration in minutes"),
    db: Session = Depends(get_db),
) -> EmployeeDocumentResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.get_by_id(
        db=db,
        document_id=document_id,
        signed_url_expiration_minutes=signed_url_expiration_minutes,
    )


@employee_documents_router.get(
    "/employee-documents/{document_id}/download",
    summary="Download document file content",
    description="Streams document binary bytes with Content-Disposition attachment for immediate browser download.",
)
def download_employee_document(
    document_id: uuid.UUID = Path(..., description="Document unique identifier"),
    db: Session = Depends(get_db),
) -> Response:
    file_bytes, filename, content_type = EMPLOYEE_DOCUMENT_SERVICE.download_file(
        db=db,
        document_id=document_id,
    )
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@employee_documents_router.get(
    "/employee-documents/{document_id}/view",
    summary="View document inline in browser",
    description="Streams document binary bytes with Content-Disposition inline (e.g. for previewing PDFs and images).",
)
def view_employee_document(
    document_id: uuid.UUID = Path(..., description="Document unique identifier"),
    db: Session = Depends(get_db),
) -> Response:
    file_bytes, filename, content_type = EMPLOYEE_DOCUMENT_SERVICE.download_file(
        db=db,
        document_id=document_id,
    )
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@employee_documents_router.put(
    "/employee-documents/{document_id}",
    response_model=EmployeeDocumentResponse,
    summary="Update employee document metadata",
    description="Updates document metadata such as title, category, or description.",
)
def update_employee_document(
    document_id: uuid.UUID = Path(..., description="Document unique identifier"),
    payload: EmployeeDocumentUpdate = Body(...),
    db: Session = Depends(get_db),
) -> EmployeeDocumentResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.update(
        db=db,
        document_id=document_id,
        request=payload,
    )


@employee_documents_router.delete(
    "/employee-documents/{document_id}",
    response_model=EmployeeDocumentDeleteResponse,
    summary="Delete employee document",
    description="Permanently deletes the document from Google Cloud Storage and removes its record from the database.",
)
def delete_employee_document(
    document_id: uuid.UUID = Path(..., description="Document unique identifier"),
    db: Session = Depends(get_db),
) -> EmployeeDocumentDeleteResponse:
    return EMPLOYEE_DOCUMENT_SERVICE.delete(
        db=db,
        document_id=document_id,
    )
