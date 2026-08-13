from collections.abc import Sequence
from uuid import UUID

from app.core.exceptions import (
    AlreadyMemberError,
    ProjectAccessDeniedError,
    ProjectNotFoundError,
    ProjectOwnerRequiredError,
    UserNotFoundError,
)
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Business logic / use cases, including access-permission resolution.

    Every method that takes a `user_id` alongside a `project_id` enforces the
    corresponding permission rule (has access / is owner) before returning.
    """

    def __init__(self, repository: ProjectRepository, user_repository: UserRepository) -> None:
        self._repo = repository
        self._users = user_repository

    async def _get_or_404(self, project_id: UUID) -> Project:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def _check_access(self, project: Project, user_id: UUID) -> None:
        if project.owner_id == user_id:
            return
        if await self._repo.get_membership(project.id, user_id) is None:
            raise ProjectAccessDeniedError()

    def _check_owner(self, project: Project, user_id: UUID) -> None:
        if project.owner_id != user_id:
            raise ProjectOwnerRequiredError()

    async def create(self, data: ProjectCreate, owner: User) -> Project:
        project = Project(name=data.name, description=data.description, owner_id=owner.id)
        return await self._repo.add(project)

    async def list_for_user(self, user_id: UUID) -> Sequence[Project]:
        return await self._repo.list_for_user(user_id)

    async def get_info(self, project_id: UUID, user_id: UUID) -> Project:
        project = await self._get_or_404(project_id)
        await self._check_access(project, user_id)
        return project

    async def update_info(self, project_id: UUID, user_id: UUID, data: ProjectUpdate) -> Project:
        project = await self._get_or_404(project_id)
        await self._check_access(project, user_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(project, field, value)
        return await self._repo.save(project)

    async def delete(self, project_id: UUID, user_id: UUID) -> Project:
        project = await self._get_or_404(project_id)
        self._check_owner(project, user_id)
        await self._repo.delete(project)
        return project

    async def invite(self, project_id: UUID, owner_id: UUID, login: str) -> ProjectMember:
        project = await self._get_or_404(project_id)
        self._check_owner(project, owner_id)

        target = await self._users.get_by_login(login)
        if target is None:
            raise UserNotFoundError(login)
        if target.id == project.owner_id or await self._repo.get_membership(project_id, target.id):
            raise AlreadyMemberError(login)

        member = ProjectMember(project_id=project_id, user_id=target.id)
        return await self._repo.add_member(member)

    async def ensure_access(self, project_id: UUID, user_id: UUID) -> Project:
        """Used by document endpoints to authorize project-scoped operations."""
        project = await self._get_or_404(project_id)
        await self._check_access(project, user_id)
        return project
