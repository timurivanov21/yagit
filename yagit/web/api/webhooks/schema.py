from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict


class Commit(BaseModel):
    id: str
    message: str
    url: HttpUrl
    timestamp: str
    author: Dict[str, str]  # name, email


class ProjectInfo(BaseModel):
    name: str
    git_http_url: HttpUrl


class GitlabPushPayload(BaseModel):
    ref: str
    before: str
    after: str
    created: Optional[bool] = False
    deleted: Optional[bool] = False
    project: ProjectInfo
    commits: List[Commit] = []
