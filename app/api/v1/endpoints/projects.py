from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUserDep, DocumentServiceDep, ProjectServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.document import DocumentRead
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectWithDocuments

router = APIRouter(tags=["projects"])


@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project (creator becomes the owner)",
)
async def create_project(
    payload: ProjectCreate, current_user: CurrentUserDep, service: ProjectServiceDep
) -> ProjectRead:
    return ProjectRead.model_validate(await service.create(payload, current_user))


@router.get(
    "/projects",
    response_model=list[ProjectWithDocuments],
    summary="List all projects accessible to the current user",
)
async def list_projects(
    current_user: CurrentUserDep, service: ProjectServiceDep
) -> list[ProjectWithDocuments]:
    projects = await service.list_for_user(current_user.id)
    return [ProjectWithDocuments.model_validate(p) for p in projects]


@router.get(
    "/project/{project_id}/info",
    response_model=ProjectRead,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_project_info(
    project_id: UUID, current_user: CurrentUserDep, service: ProjectServiceDep
) -> ProjectRead:
    return ProjectRead.model_validate(await service.get_info(project_id, current_user.id))


@router.put(
    "/project/{project_id}/info",
    response_model=ProjectRead,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_project_info(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: CurrentUserDep,
    service: ProjectServiceDep,
) -> ProjectRead:
    project = await service.update_info(project_id, current_user.id, payload)
    return ProjectRead.model_validate(project)


@router.delete(
    "/project/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project and its documents (owner only)",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
    document_service: DocumentServiceDep,
) -> None:
    await project_service.delete(project_id, current_user.id)
    await document_service.delete_project_files(project_id)


@router.get(
    "/project/{project_id}/documents",
    response_model=list[DocumentRead],
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def list_project_documents(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
    document_service: DocumentServiceDep,
) -> list[DocumentRead]:
    await project_service.ensure_access(project_id, current_user.id)
    documents = await document_service.list_for_project(project_id)
    return [DocumentRead.model_validate(d) for d in documents]


@router.post(
    "/project/{project_id}/documents",
    response_model=list[DocumentRead],
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more documents (docx, pdf) to a project",
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def upload_project_documents(
    project_id: UUID,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
    document_service: DocumentServiceDep,
    files: Annotated[list[UploadFile], File()],
) -> list[DocumentRead]:
    await project_service.ensure_access(project_id, current_user.id)
    documents = await document_service.upload(project_id, files)
    return [DocumentRead.model_validate(d) for d in documents]


@router.post(
    "/project/{project_id}/invite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Grant a user access to the project (owner only)",
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def invite_user(
    project_id: UUID,
    user: str,
    current_user: CurrentUserDep,
    service: ProjectServiceDep,
) -> None:
    await service.invite(project_id, current_user.id, user)
