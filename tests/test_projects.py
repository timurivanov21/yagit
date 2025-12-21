import pytest
from faker import Faker
from httpx import HTTPStatusError, Request, Response
from pytest_mock import MockerFixture
from sqlalchemy import select
from starlette import status

from yagit.db.models.project import Project

faker = Faker()


def make_test_cases(count: int = 7):
    cases = []

    for _ in range(count):
        payload = {
            "name": faker.unique.company(),
            "gitlab_token": faker.uuid4(),
            "tracker_token": faker.uuid4(),
            "tracker_org_id": faker.uuid4(),
        }

        gitlab_projects = [
            {
                "gitlab_project_id": faker.random_int(min=1, max=10_000),
                "name": faker.slug(),
            }
            for _ in range(faker.random_int(min=1, max=5))
        ]

        cases.append(
            pytest.param(
                payload,
                gitlab_projects,
                id=f"repos={len(gitlab_projects)}",
            ),
        )

    return cases


INVALID_PAYLOADS = [
    pytest.param(
        {
            "gitlab_token": "token",
            "tracker_token": "tracker-token",
            "tracker_org_id": "org-123",
        },
        "name",
        id="missing-name",
    ),
    pytest.param(
        {
            "name": "Project without gitlab token",
            "tracker_token": "tracker-token",
            "tracker_org_id": "org-123",
        },
        "gitlab_token",
        id="missing-gitlab-token",
    ),
    pytest.param(
        {
            "name": "Project without tracker token",
            "gitlab_token": "token",
            "tracker_org_id": "org-123",
        },
        "tracker_token",
        id="missing-tracker-token",
    ),
    pytest.param(
        {
            "name": "Project without tracker org id",
            "gitlab_token": "token",
            "tracker_token": "tracker-token",
        },
        "tracker_org_id",
        id="missing-tracker-org-id",
    ),
]
CREATE_PROJECT_CASES = make_test_cases()
PROJECT_COUNTS = [
    pytest.param(0, id="no-projects"),
    pytest.param(1, id="one-project"),
    pytest.param(3, id="three-projects"),
    pytest.param(5, id="five-projects"),
]
DELETE_CASES = [
    pytest.param(1, 0, id="single-project"),
    pytest.param(3, 0, id="first-of-many"),
    pytest.param(3, 1, id="middle-of-many"),
    pytest.param(3, 2, id="last-of-many"),
]
TRACKER_BOARDS_CASES = [
    pytest.param(
        [
            {
                "id": 1,
                "name": "Board 1",
                "columns": [
                    {"id": "c1", "display": "To Do"},
                    {"id": "c2", "display": "In Progress"},
                ],
            },
        ],
        id="one-board-with-columns",
    ),
    pytest.param(
        [
            {
                "id": 10,
                "name": "Board without columns",
                "columns": [],
            },
        ],
        id="board-without-columns",
    ),
    pytest.param(
        [
            {
                "id": 1,
                "name": "Board 1",
            },
            {
                "id": 2,
                "name": "Board 2",
                "columns": [
                    {"id": "c1", "display": "Done"},
                ],
            },
        ],
        id="multiple-boards-mixed",
    ),
]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload, gitlab_projects",
    CREATE_PROJECT_CASES,
)
async def test_create_project_success(
    client,
    dbsession,
    mocker: MockerFixture,
    payload,
    gitlab_projects,
):
    mock_gl = mocker.patch(
        "yagit.web.api.projects.views.GitLabClient",
        autospec=True,
    )

    gl_instance = mock_gl.return_value.__aenter__.return_value
    gl_instance.list_projects.return_value = gitlab_projects

    response = await client.post("/api/projects/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    body = response.json()
    assert body["repositories"] == gitlab_projects
    assert isinstance(body["project_id"], int)

    result = await dbsession.execute(
        select(Project).where(Project.name == payload["name"]),
    )
    project = result.scalar_one()

    assert project.gitlab_token == payload["gitlab_token"]
    assert project.tracker_token == payload["tracker_token"]


@pytest.mark.anyio
async def test_create_project_invalid_gitlab_token(
    client,
    mocker: MockerFixture,
):
    mock_gl = mocker.patch(
        "yagit.web.api.projects.views.GitLabClient",
        autospec=True,
    )

    mock_gl_instance = mock_gl.return_value.__aenter__.return_value

    mock_gl_instance.list_projects.side_effect = HTTPStatusError(
        message="Unauthorized",
        request=Request("GET", "https://gitlab.com/api"),
        response=Response(status_code=status.HTTP_401_UNAUTHORIZED),
    )

    payload = {
        "name": "Bad project",
        "gitlab_token": "invalid-token",
        "tracker_token": "tracker-token",
        "tracker_org_id": "org-123",
    }

    response = await client.post("/api/projects/", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "invalid token"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload, missing_field",
    INVALID_PAYLOADS,
)
async def test_create_project_validation_error_missing_fields(
    client,
    mocker: MockerFixture,
    payload,
    missing_field,
):
    mock_gl = mocker.patch(
        "yagit.web.api.projects.views.GitLabClient",
        autospec=True,
    )

    response = await client.post("/api/projects/", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    body = response.json()

    error_fields = [
        err["loc"][-1] for err in body["detail"] if err["type"] == "missing"
    ]

    assert missing_field in error_fields

    mock_gl.assert_not_called()


@pytest.mark.anyio
async def test_get_project_success(
    client,
    dbsession,
):
    project = Project(
        name="Test project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-123",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    response = await client.get(f"/api/projects/{project.id}")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert body["id"] == project.id
    assert body["name"] == project.name


@pytest.mark.anyio
async def test_get_project_not_found(
    client,
):
    response = await client.get("/api/projects/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "projects_count",
    PROJECT_COUNTS,
)
async def test_list_projects(
    client,
    dbsession,
    projects_count: int,
):
    projects = []

    for i in range(projects_count):
        project = Project(
            name=f"Project {i}",
            gitlab_token=f"gitlab-token-{i}",
            tracker_token=f"tracker-token-{i}",
            tracker_org_id=f"org-{i}",
        )
        projects.append(project)
        dbsession.add(project)

    if projects:
        await dbsession.commit()
        for project in projects:
            await dbsession.refresh(project)

    response = await client.get("/api/projects/")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == projects_count

    returned_ids = {item["id"] for item in body}
    expected_ids = {project.id for project in projects}

    assert returned_ids == expected_ids


@pytest.mark.anyio
@pytest.mark.parametrize(
    "projects_count, delete_index",
    DELETE_CASES,
)
async def test_delete_project_success(
    client,
    dbsession,
    projects_count: int,
    delete_index: int,
):
    projects = []

    for i in range(projects_count):
        project = Project(
            name=f"Project {i}",
            gitlab_token=f"gitlab-token-{i}",
            tracker_token=f"tracker-token-{i}",
            tracker_org_id=f"org-{i}",
        )
        dbsession.add(project)
        projects.append(project)

    await dbsession.commit()
    for project in projects:
        await dbsession.refresh(project)

    project_to_delete = projects[delete_index]

    response = await client.delete(f"/api/projects/{project_to_delete.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    deleted = await dbsession.get(Project, project_to_delete.id)
    assert deleted is None

    remaining_ids = {p.id for p in await dbsession.scalars(select(Project))}
    expected_ids = {p.id for p in projects if p.id != project_to_delete.id}

    assert remaining_ids == expected_ids


@pytest.mark.anyio
async def test_delete_project_not_found(
    client,
):
    response = await client.delete("/api/projects/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "boards_raw",
    TRACKER_BOARDS_CASES,
)
async def test_get_tracker_boards_success(
    client,
    dbsession,
    mocker: MockerFixture,
    boards_raw,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    mock_tracker = mocker.patch(
        "yagit.web.api.projects.views.TrackerClient",
        autospec=True,
    )

    tr_instance = mock_tracker.return_value.__aenter__.return_value
    tr_instance.list_boards.return_value = boards_raw

    response = await client.get(f"/api/projects/{project.id}/tracker_boards")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert len(body) == len(boards_raw)

    for returned, raw in zip(body, boards_raw):
        assert returned["id"] == raw["id"]
        assert returned["name"] == raw.get("name", "")

        expected_columns = raw.get("columns", [])
        assert len(returned["columns"]) == len(expected_columns)

        for col, raw_col in zip(returned["columns"], expected_columns):
            assert col["id"] == raw_col["id"]
            assert col["name"] == raw_col.get("display", "")


@pytest.mark.anyio
async def test_get_tracker_boards_project_not_found(
    client,
):
    response = await client.get("/api/projects/999999/tracker_boards")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "project_id",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
    ],
)
async def test_get_tracker_boards_invalid_project_id(
    client,
    project_id: int,
):
    response = await client.get(f"/api/projects/{project_id}/tracker_boards")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
