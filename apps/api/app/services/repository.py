from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.repositories.project import ProjectRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate


class RepositoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo_repo = RepositoryRepository(session)
        self.project_repo = ProjectRepository(session)

    async def _verify_project_ownership(
        self, user_id: str, project_id: str, missing: str = "Project not found"
    ) -> None:
        # 404 (not 422) for other users' records, consistent with the rest of the API and without revealing existence.
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise NotFoundError(missing)

    async def create(self, user_id: str, project_id: str, data: RepositoryCreate) -> RepositoryResponse:
        await self._verify_project_ownership(user_id, project_id)

        repo_data = data.model_dump()
        repo_data["project_id"] = project_id

        repo = await self.repo_repo.create(repo_data)
        return RepositoryResponse.model_validate(repo)

    async def get(self, user_id: str, repository_id: str) -> RepositoryResponse:
        repo = await self.repo_repo.get_by_id(repository_id)
        if not repo:
            raise NotFoundError("Repository not found")

        await self._verify_project_ownership(user_id, str(repo.project_id), missing="Repository not found")

        return RepositoryResponse.model_validate(repo)

    async def update(self, user_id: str, repository_id: str, data: RepositoryUpdate) -> RepositoryResponse:
        repo = await self.repo_repo.get_by_id(repository_id)
        if not repo:
            raise NotFoundError("Repository not found")

        await self._verify_project_ownership(user_id, str(repo.project_id), missing="Repository not found")

        update_data = data.model_dump(exclude_unset=True)
        repo = await self.repo_repo.update(repo, update_data)
        return RepositoryResponse.model_validate(repo)

    async def delete(self, user_id: str, repository_id: str) -> None:
        repo = await self.repo_repo.get_by_id(repository_id)
        if not repo:
            raise NotFoundError("Repository not found")

        await self._verify_project_ownership(user_id, str(repo.project_id), missing="Repository not found")

        await self.repo_repo.delete(repo.id)

    async def list_by_project(self, user_id: str, project_id: str) -> list[RepositoryResponse]:
        await self._verify_project_ownership(user_id, project_id)

        repos = await self.repo_repo.list_by_project(project_id)
        return [RepositoryResponse.model_validate(r) for r in repos]
