"""
app/dependencies.py
--------------------
FastAPI shared dependency providers.

Responsibilities:
- Provide the Settings / configuration object via FastAPI Depends
- Provide a module-level logger
- Construct and provide fully wired service instances
- Keep all wiring in one place so the API layer remains free of
  construction logic
"""

import logging

from app.core.config import settings
from app.core.settings import Settings
from services.git_service import GitService
from services.github_service import GitHubService
from services.parser_service import ParserService
from services.repository_service import RepositoryService
from services.workflow_service import WorkflowService
from workflow.workflow_manager import WorkflowManager


# ---------------------------------------------------------------------------
# Logger dependency
# ---------------------------------------------------------------------------

def get_logger(name: str = "app") -> logging.Logger:
    """Return a named logger instance.

    Args:
        name: Logger namespace; defaults to 'app'.

    Returns:
        logging.Logger: The logger for the given namespace.
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Settings dependency
# ---------------------------------------------------------------------------

def get_settings() -> Settings:
    """Return the application settings singleton.

    This is exposed as a FastAPI dependency so endpoints can receive
    configuration via ``Depends(get_settings)``.

    Returns:
        Settings: The application configuration object.
    """
    return settings


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------

def get_repository_service() -> RepositoryService:
    """Construct and return a RepositoryService instance.

    Returns:
        RepositoryService: Configured with the repository root from settings.
    """
    return RepositoryService(repository_root=settings.repository_root)


def get_git_service() -> GitService:
    """Construct and return a GitService instance.

    Returns:
        GitService: Configured with the repository root from settings.
    """
    return GitService(repository_root=settings.repository_root)


def get_workflow_manager() -> WorkflowManager:
    """Construct and return a WorkflowManager instance.

    Returns:
        WorkflowManager: Configured with the workflow directory from settings.
    """
    return WorkflowManager(workflow_dir=settings.workflow_path)


def get_workflow_service() -> WorkflowService:
    """Construct and return a WorkflowService instance.

    Returns:
        WorkflowService: Wrapping a fresh WorkflowManager.
    """
    return WorkflowService(workflow_manager=get_workflow_manager())


def get_parser_service() -> ParserService:
    """Construct and return a ParserService instance.

    Returns:
        ParserService: Stateless parser with no configuration.
    """
    return ParserService()


def get_github_service() -> GitHubService:
    """Construct and return a fully wired GitHubService instance.

    All sub-services are constructed here so the API layer only
    needs to declare ``Depends(get_github_service)``.

    Returns:
        GitHubService: Orchestrator wired with all required services.
    """
    return GitHubService(
        git_service=get_git_service(),
        parser_service=get_parser_service(),
        workflow_service=get_workflow_service(),
        repository_service=get_repository_service(),
        github_secret=settings.github_secret,
    )
