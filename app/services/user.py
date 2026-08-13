from uuid import UUID

from app.core.exceptions import DuplicateUserError, InvalidCredentialsError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class UserService:
    """Business logic / use cases. Raises domain errors, knows nothing about HTTP."""

    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def register(self, data: UserCreate) -> User:
        if await self._repo.get_by_login(data.login) is not None:
            raise DuplicateUserError(data.login)
        user = User(login=data.login, password_hash=hash_password(data.password))
        return await self._repo.add(user)

    async def authenticate(self, login: str, password: str) -> User:
        user = await self._repo.get_by_login(login)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._repo.get_by_id(user_id)

    async def get_by_login(self, login: str) -> User | None:
        return await self._repo.get_by_login(login)
