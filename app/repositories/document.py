from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: UUID) -> Document | None:
        return await self._session.get(Document, document_id)

    async def list_for_project(self, project_id: UUID) -> Sequence[Document]:
        result = await self._session.execute(
            select(Document).where(Document.project_id == project_id).order_by(Document.created_at)
        )
        return result.scalars().all()

    async def add(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def save(self, document: Document) -> Document:
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self._session.delete(document)
        await self._session.flush()
