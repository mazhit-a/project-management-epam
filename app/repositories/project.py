from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectMember


class ProjectRepository:
    """Data access only. Never raises domain/HTTP errors, never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def list_for_user(self, user_id: UUID) -> Sequence[Project]:
        """Projects the user owns or has been granted access to, documents included."""
        member_project_ids = select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id
        )
        stmt = (
            select(Project)
            .where(or_(Project.owner_id == user_id, Project.id.in_(member_project_ids)))
            .options(selectinload(Project.documents))
            .order_by(Project.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_membership(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        result = await self._session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def add(self, project: Project) -> Project:
        self._session.add(project)
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def save(self, project: Project) -> Project:
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.flush()

    async def add_member(self, member: ProjectMember) -> ProjectMember:
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member
