import uuid
from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.core import storage
from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    UnsupportedDocumentTypeError,
)
from app.models.document import Document
from app.repositories.document import DocumentRepository

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentService:
    """Business logic / use cases. Owns both the DB rows and the stored files."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repo = repository

    async def list_for_project(self, project_id: UUID) -> Sequence[Document]:
        return await self._repo.list_for_project(project_id)

    async def get(self, document_id: UUID) -> Document:
        document = await self._repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        return document

    async def _read_and_validate(self, upload: UploadFile) -> tuple[bytes, str, str]:
        extension = Path(upload.filename or "").suffix.lower()
        content_type = ALLOWED_EXTENSIONS.get(extension)
        if content_type is None:
            raise UnsupportedDocumentTypeError(extension or "unknown")

        data = await upload.read()
        if len(data) > settings.MAX_UPLOAD_SIZE:
            raise DocumentTooLargeError(len(data), settings.MAX_UPLOAD_SIZE)
        return data, extension, content_type

    async def upload(self, project_id: UUID, files: list[UploadFile]) -> list[Document]:
        created: list[Document] = []
        for upload in files:
            data, extension, content_type = await self._read_and_validate(upload)
            document_id = uuid.uuid4()
            path = storage.project_directory(project_id) / f"{document_id}{extension}"
            await storage.save_file(path, data)

            document = Document(
                id=document_id,
                project_id=project_id,
                filename=upload.filename or f"{document_id}{extension}",
                content_type=content_type,
                size=len(data),
                storage_path=str(path),
            )
            created.append(await self._repo.add(document))
        return created

    async def replace(self, document_id: UUID, upload: UploadFile) -> Document:
        document = await self.get(document_id)
        data, extension, content_type = await self._read_and_validate(upload)

        old_path = Path(document.storage_path)
        new_path = old_path.with_suffix(extension)
        await storage.save_file(new_path, data)
        if new_path != old_path:
            await storage.delete_file(old_path)

        document.filename = upload.filename or document.filename
        document.content_type = content_type
        document.size = len(data)
        document.storage_path = str(new_path)
        return await self._repo.save(document)

    async def delete(self, document_id: UUID) -> Document:
        document = await self.get(document_id)
        await self._repo.delete(document)
        await storage.delete_file(Path(document.storage_path))
        return document

    async def delete_project_files(self, project_id: UUID) -> None:
        await storage.delete_directory(storage.project_directory(project_id))
