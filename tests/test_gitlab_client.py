from unittest.mock import AsyncMock, MagicMock

import pytest

from yagit.services.gitlab_client import GitLabClient
from yagit.web.api.projects.schema import GitLabProject

VERIFY_TOKEN_CASES = [
    pytest.param("abc", "abc", True, id="same-tokens"),
    pytest.param("abc", "def", False, id="different-tokens"),
    pytest.param("", "", True, id="both-empty"),
    pytest.param(None, None, True, id="both-none"),
    pytest.param("abc", None, False, id="header-only"),
    pytest.param(None, "abc", False, id="expected-only"),
]


@pytest.fixture
def gitlab_client(mocker):
    client = GitLabClient(token="token")

    client.list_hooks = AsyncMock()
    client._client = MagicMock()
    client._client.post = AsyncMock()
    client._client.put = AsyncMock()

    return client


@pytest.mark.anyio
async def test_gitlab_client_get(
    mock_httpx_client,
    mock_response,
):
    client = GitLabClient(token="token")

    result = await client._get("/projects/1")

    mock_httpx_client.get.assert_awaited_once_with("/projects/1")
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()

    assert result == {"ok": True}


@pytest.mark.anyio
async def test_gitlab_client_post(
    mock_httpx_client,
    mock_response,
):
    client = GitLabClient(token="token")

    payload = {"a": 1}

    result = await client._post("/projects", json=payload)

    mock_httpx_client.post.assert_awaited_once_with(
        "/projects",
        json=payload,
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()

    assert result == {"ok": True}


@pytest.mark.anyio
async def test_gitlab_client_put(
    mock_httpx_client,
    mock_response,
):
    client = GitLabClient(token="token")

    payload = {"b": 2}

    result = await client._put("/projects/1", json=payload)

    mock_httpx_client.put.assert_awaited_once_with(
        "/projects/1",
        json=payload,
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()

    assert result == {"ok": True}


import httpx


@pytest.mark.anyio
async def test_gitlab_client_get_raises_http_error(
    mock_httpx_client,
    mock_response,
):
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Forbidden",
        request=httpx.Request("GET", "url"),
        response=httpx.Response(403),
    )

    client = GitLabClient(token="token")

    with pytest.raises(httpx.HTTPStatusError):
        await client._get("/projects/1")


@pytest.mark.anyio
async def test_list_branches(
    mocker,
):
    client = GitLabClient(token="token")

    mocker.patch.object(
        client,
        "_get",
        AsyncMock(
            return_value=[
                {"name": "main"},
                {"name": "develop"},
                {"name": "feature/test"},
            ],
        ),
    )

    branches = await client.list_branches(project_id=123)

    client._get.assert_awaited_once_with("/projects/123/repository/branches")

    assert branches == ["main", "develop", "feature/test"]


@pytest.mark.anyio
async def test_list_projects(
    mocker,
):
    client = GitLabClient(token="token")

    api_response = [
        {"id": 1, "name": "Project One"},
        {"id": 2, "name": "Project Two"},
    ]

    mocker.patch.object(
        client,
        "_get",
        AsyncMock(return_value=api_response),
    )

    projects = await client.list_projects()

    client._get.assert_awaited_once_with(
        "/projects",
        params={
            "archived": "false",
            "owned": "true",
            "simple": "true",
        },
    )

    assert projects == [
        GitLabProject(gitlab_project_id=1, name="Project One"),
        GitLabProject(gitlab_project_id=2, name="Project Two"),
    ]


@pytest.mark.anyio
async def test_list_projects_empty(
    mocker,
):
    client = GitLabClient(token="token")

    mocker.patch.object(
        client,
        "_get",
        AsyncMock(return_value=[]),
    )

    projects = await client.list_projects()

    assert projects == []


@pytest.mark.parametrize(
    "header_token, expected_token, result",
    VERIFY_TOKEN_CASES,
)
def test_verify_gitlab_token(header_token, expected_token, result):
    assert GitLabClient.verify_gitlab_token(header_token, expected_token) is result


@pytest.mark.anyio
async def test_ensure_hook_creates_hook(
    gitlab_client,
):
    gitlab_client.list_hooks.return_value = []

    await gitlab_client.ensure_hook(
        project_id=1,
        url="https://example.com/webhook",
        secret_token="secret",
        hook_payload={"push_events": True},
    )

    gitlab_client._client.post.assert_awaited_once_with(
        "/projects/1/hooks",
        json={
            "url": "https://example.com/webhook",
            "token": "secret",
            "push_events": True,
        },
    )

    gitlab_client._client.put.assert_not_called()


@pytest.mark.anyio
async def test_ensure_hook_updates_existing_hook(
    gitlab_client,
):
    gitlab_client.list_hooks.return_value = [
        {
            "id": 42,
            "url": "https://example.com/webhook",
        },
    ]

    await gitlab_client.ensure_hook(
        project_id=1,
        url="https://example.com/webhook",
        secret_token="secret",
        hook_payload={"merge_requests_events": True},
    )

    gitlab_client._client.put.assert_awaited_once_with(
        "/projects/1/hooks/42",
        json={
            "url": "https://example.com/webhook",
            "token": "secret",
            "merge_requests_events": True,
        },
    )

    gitlab_client._client.post.assert_not_called()


@pytest.mark.anyio
async def test_ensure_hook_ignores_other_hooks(
    gitlab_client,
):
    gitlab_client.list_hooks.return_value = [
        {"id": 1, "url": "https://other.com/hook"},
        {"id": 2, "url": "https://another.com/hook"},
    ]

    await gitlab_client.ensure_hook(
        project_id=1,
        url="https://example.com/webhook",
        secret_token="secret",
        hook_payload={"push_events": True},
    )

    gitlab_client._client.post.assert_awaited_once()
    gitlab_client._client.put.assert_not_called()
