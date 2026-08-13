from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.services.document import DocumentService
from app.services.project import ProjectService
from app.services.user import UserService

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# --- wiring: session -> repository -> service ---------------------------------


def get_user_repository(session: DbSession) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(repository: UserRepositoryDep) -> UserService:
    return UserService(repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_project_repository(session: DbSession) -> ProjectRepository:
    return ProjectRepository(session)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_project_service(
    repository: ProjectRepositoryDep, user_repository: UserRepositoryDep
) -> ProjectService:
    return ProjectService(repository, user_repository)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_document_repository(session: DbSession) -> DocumentRepository:
    return DocumentRepository(session)


DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]


def get_document_service(repository: DocumentRepositoryDep) -> DocumentService:
    return DocumentService(repository)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]


# --- authentication -------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=True, description="JWT issued by POST /login")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    user_service: UserServiceDep,
) -> User:
    user_id = decode_access_token(credentials.credentials)
    user = await user_service.get_by_id(user_id)
    if user is None:
        raise AuthenticationError("User no longer exists")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
