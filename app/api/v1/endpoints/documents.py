from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUserDep, DocumentServiceDep, ProjectServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.document import DocumentRead

router = APIRouter(tags=["documents"])


@router.get(
    "/document/{document_id}",
    summary="Download a document, if the user has access to its project",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def download_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    project_service: ProjectServiceDep,
) -> FileResponse:
    document = await document_service.get(document_id)
    await project_service.ensure_access(document.project_id, current_user.id)
    return FileResponse(
        path=document.storage_path,
        filename=document.filename,
        media_type=document.content_type,
    )


@router.put(
    "/document/{document_id}",
    response_model=DocumentRead,
    summary="Replace a document's file contents",
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def update_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    project_service: ProjectServiceDep,
    file: Annotated[UploadFile, File()],
) -> DocumentRead:
    document = await document_service.get(document_id)
    await project_service.ensure_access(document.project_id, current_user.id)
    updated = await document_service.replace(document_id, file)
    return DocumentRead.model_validate(updated)


@router.delete(
    "/document/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    project_service: ProjectServiceDep,
) -> None:
    document = await document_service.get(document_id)
    await project_service.ensure_access(document.project_id, current_user.id)
    await document_service.delete(document_id)
