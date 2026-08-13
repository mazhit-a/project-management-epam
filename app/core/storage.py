"""Async filesystem helpers for storing uploaded project documents.

Layout: {STORAGE_DIR}/{project_id}/{document_id}{ext}
Keeping every project's files under its own directory lets project deletion
clean up storage with a single recursive remove instead of enumerating rows.
"""

import asyncio
import contextlib
import shutil
from pathlib import Path
from uuid import UUID

import aiofiles
import aiofiles.os

from app.core.config import settings


def project_directory(project_id: UUID) -> Path:
    return Path(settings.STORAGE_DIR) / str(project_id)


async def save_file(path: Path, data: bytes) -> None:
    await aiofiles.os.makedirs(path.parent, exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)


async def delete_file(path: Path) -> None:
    with contextlib.suppress(FileNotFoundError):
        await aiofiles.os.remove(path)


async def delete_directory(path: Path) -> None:
    await asyncio.to_thread(shutil.rmtree, path, True)
