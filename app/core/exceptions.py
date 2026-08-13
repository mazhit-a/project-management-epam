"""Domain exceptions.

These deliberately know NOTHING about HTTP. The API layer is responsible for
translating them into status codes (see app/api/errors.py). That is what keeps
the service layer reusable from a CLI, a worker, or a test.
"""

from typing import Any
from uuid import UUID


class DomainError(Exception):
    code: str = "domain_error"
    message: str = "A domain error occurred"

    def __init__(self, message: str | None = None, **context: Any) -> None:
        self.message = message or self.message
        self.context = context
        super().__init__(self.message)


class EntityNotFoundError(DomainError):
    code = "not_found"
    message = "Entity not found"


class EntityAlreadyExistsError(DomainError):
    code = "already_exists"
    message = "Entity already exists"


class BusinessRuleViolationError(DomainError):
    code = "business_rule_violation"
    message = "Business rule violated"


class AuthenticationError(DomainError):
    code = "authentication_failed"
    message = "Authentication failed"


class AuthorizationError(DomainError):
    code = "authorization_failed"
    message = "You do not have access to this resource"


# --- Auth / user ---------------------------------------------------------------


class InvalidCredentialsError(AuthenticationError):
    code = "invalid_credentials"

    def __init__(self) -> None:
        super().__init__("Invalid login or password")


class DuplicateUserError(EntityAlreadyExistsError):
    code = "duplicate_user"

    def __init__(self, login: str) -> None:
        super().__init__(f"A user with login '{login}' already exists", login=login)


class UserNotFoundError(EntityNotFoundError):
    code = "user_not_found"

    def __init__(self, login: str) -> None:
        super().__init__(f"User '{login}' was not found", login=login)


# --- Projects --------------------------------------------------------------------


class ProjectNotFoundError(EntityNotFoundError):
    code = "project_not_found"

    def __init__(self, project_id: UUID) -> None:
        super().__init__(f"Project '{project_id}' was not found", project_id=str(project_id))


class ProjectAccessDeniedError(AuthorizationError):
    code = "project_access_denied"

    def __init__(self) -> None:
        super().__init__("You do not have access to this project")


class ProjectOwnerRequiredError(AuthorizationError):
    code = "project_owner_required"

    def __init__(self) -> None:
        super().__init__("Only the project owner can perform this action")


class AlreadyMemberError(BusinessRuleViolationError):
    code = "already_member"

    def __init__(self, login: str) -> None:
        super().__init__(f"User '{login}' already has access to this project", login=login)


# --- Documents -------------------------------------------------------------------


class DocumentNotFoundError(EntityNotFoundError):
    code = "document_not_found"

    def __init__(self, document_id: UUID) -> None:
        super().__init__(f"Document '{document_id}' was not found", document_id=str(document_id))


class UnsupportedDocumentTypeError(BusinessRuleViolationError):
    code = "unsupported_document_type"

    def __init__(self, extension: str) -> None:
        super().__init__(
            f"Document type '{extension}' is not supported (allowed: .pdf, .docx)",
            extension=extension,
        )


class DocumentTooLargeError(BusinessRuleViolationError):
    code = "document_too_large"

    def __init__(self, size: int, max_size: int) -> None:
        super().__init__(
            f"Document size {size} bytes exceeds the maximum allowed size {max_size} bytes",
            size=size,
            max_size=max_size,
        )
