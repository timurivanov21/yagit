import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select
from starlette import status

from yagit.db.models.automation_rule import GitEventType, AutomationRule
from yagit.db.models.project import Project

CREATE_RULE_CASES = [
    pytest.param(
        {
            "event_type": GitEventType.PUSH.value,
            "target_branch": None,
        },
        id="push-without-branch",
    ),
    pytest.param(
        {
            "event_type": GitEventType.BRANCH_CREATE.value,
            "target_branch": None,
        },
        id="branch-create-without-branch",
    ),
    pytest.param(
        {
            "event_type": GitEventType.MERGE_REQUEST_OPENED.value,
            "target_branch": "main",
        },
        id="mr-opened-with-branch",
    ),
    pytest.param(
        {
            "event_type": GitEventType.MERGE_REQUEST_MERGED.value,
            "target_branch": "develop",
        },
        id="mr-merged-with-branch",
    ),
]
INVALID_RULE_PAYLOADS = [
    pytest.param(
        {
            # event_type missing
            "tracker_column_id": "col-1",
            "tracker_board_id": 1,
            "gitlab_project_id": 1,
        },
        "event_type",
        id="missing-event-type",
    ),
    pytest.param(
        {
            "event_type": GitEventType.PUSH.value,
            # tracker_column_id missing
            "tracker_board_id": 1,
            "gitlab_project_id": 1,
        },
        "tracker_column_id",
        id="missing-tracker-column-id",
    ),
    pytest.param(
        {
            "event_type": GitEventType.PUSH.value,
            "tracker_column_id": "col-1",
            # tracker_board_id missing
            "gitlab_project_id": 1,
        },
        "tracker_board_id",
        id="missing-tracker-board-id",
    ),
    pytest.param(
        {
            "event_type": GitEventType.PUSH.value,
            "tracker_column_id": "col-1",
            "tracker_board_id": 1,
            # gitlab_project_id missing
        },
        "gitlab_project_id",
        id="missing-gitlab-project-id",
    ),
]
LIST_RULES_CASES = [
    pytest.param(0, id="no-rules"),
    pytest.param(1, id="one-rule"),
    pytest.param(3, id="multiple-rules"),
]
DELETE_RULE_CASES = [
    pytest.param(1, id="single-rule"),
    pytest.param(3, id="multiple-rules"),
]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "rule_data",
    CREATE_RULE_CASES,
)
async def test_create_rule_success(
    client,
    dbsession,
    mocker: MockerFixture,
    rule_data,
):
    mocker.patch(
        "yagit.web.api.rules.views._sync_webhook",
        autospec=True,
    )

    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    payload = {
        **rule_data,
        "tracker_column_id": "col-1",
        "tracker_board_id": 10,
        "gitlab_project_id": 100,
    }

    response = await client.post(
        f"/api/projects/{project.id}/rules/",
        json=payload,
    )

    assert response.status_code == status.HTTP_201_CREATED

    body = response.json()
    assert body["event_type"] == rule_data["event_type"]
    assert body["target_branch"] == rule_data["target_branch"]
    assert body["tracker_column_id"] == payload["tracker_column_id"]
    assert "id" in body

    rule = await dbsession.get(AutomationRule, body["id"])
    assert rule is not None
    assert rule.project_id == project.id


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload, missing_field",
    INVALID_RULE_PAYLOADS,
)
async def test_create_rule_validation_error_missing_required_fields(
    client,
    dbsession,
    payload,
    missing_field,
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

    response = await client.post(
        f"/api/projects/{project.id}/rules/",
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    detail = response.json()["detail"]
    error_fields = [
        err["loc"][-1]
        for err in detail
        if err["type"] == "missing"
    ]

    assert missing_field in error_fields


@pytest.mark.anyio
async def test_create_rule_duplicate(
    client,
    dbsession,
    mocker: MockerFixture,
):
    mocker.patch(
        "yagit.web.api.rules.views._sync_webhook",
        autospec=True,
    )

    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    rule = AutomationRule(
        project_id=project.id,
        event_type=GitEventType.PUSH,
        target_branch=None,
        tracker_column_id="col-1",
    )
    dbsession.add(rule)
    await dbsession.commit()

    payload = {
        "event_type": GitEventType.PUSH.value,
        "target_branch": None,
        "tracker_column_id": "col-2",
        "tracker_board_id": 1,
        "gitlab_project_id": 1,
    }

    response = await client.post(
        f"/api/projects/{project.id}/rules/",
        json=payload,
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Rule already exists"


@pytest.mark.anyio
async def test_create_rule_merge_event_requires_target_branch_error_message(
    client,
    dbsession,
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

    payload = {
        "event_type": GitEventType.MERGE_REQUEST_OPENED.value,
        "target_branch": None,
        "tracker_column_id": "col-1",
        "tracker_board_id": 1,
        "gitlab_project_id": 1,
    }

    response = await client.post(
        f"/api/projects/{project.id}/rules/",
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    detail = response.json()["detail"]

    assert any(
        err["loc"][-1] == "target_branch"
        and "target_branch is required for merge request rules" in err["msg"]
        for err in detail
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "rules_count",
    LIST_RULES_CASES,
)
async def test_list_rules(
    client,
    dbsession,
    rules_count: int,
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

    rules = []

    for i in range(rules_count):
        rule = AutomationRule(
            project_id=project.id,
            event_type=GitEventType.PUSH,
            target_branch=None,
            tracker_column_id=f"col-{i}",
        )
        rules.append(rule)
        dbsession.add(rule)

    if rules:
        await dbsession.commit()
        for rule in rules:
            await dbsession.refresh(rule)

    response = await client.get(f"/api/projects/{project.id}/rules/")

    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == rules_count

    returned_ids = {item["id"] for item in body}
    expected_ids = {rule.id for rule in rules}

    assert returned_ids == expected_ids


@pytest.mark.anyio
async def test_list_rules_project_not_found_returns_empty_list(
    client,
):
    response = await client.get("/api/projects/999999/rules/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.anyio
@pytest.mark.parametrize(
    "rules_count",
    DELETE_RULE_CASES,
)
async def test_delete_rule_success(
    client,
    dbsession,
    rules_count: int,
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

    rules = []

    for i in range(rules_count):
        rule = AutomationRule(
            project_id=project.id,
            event_type=GitEventType.PUSH,
            target_branch=None,
            tracker_column_id=f"col-{i}",
        )
        rules.append(rule)
        dbsession.add(rule)

    await dbsession.commit()
    for rule in rules:
        await dbsession.refresh(rule)

    rule_to_delete = rules[0]

    response = await client.delete(
        f"/api/projects/{project.id}/rules/{rule_to_delete.id}"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    deleted = await dbsession.get(AutomationRule, rule_to_delete.id)
    assert deleted is None

    remaining_ids = {
        r.id for r in await dbsession.scalars(select(AutomationRule))
    }
    expected_ids = {r.id for r in rules[1:]}

    assert remaining_ids == expected_ids


@pytest.mark.anyio
async def test_delete_rule_not_found(
    client,
    dbsession,
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

    response = await client.delete(
        f"/api/projects/{project.id}/rules/999999"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Rule not found"


@pytest.mark.anyio
async def test_delete_rule_wrong_project(
    client,
    dbsession,
):
    project_1 = Project(
        name="Project 1",
        gitlab_token="gitlab-token-1",
        tracker_token="tracker-token-1",
        tracker_org_id="org-1",
    )
    project_2 = Project(
        name="Project 2",
        gitlab_token="gitlab-token-2",
        tracker_token="tracker-token-2",
        tracker_org_id="org-2",
    )
    dbsession.add_all([project_1, project_2])
    await dbsession.commit()
    await dbsession.refresh(project_1)
    await dbsession.refresh(project_2)

    rule = AutomationRule(
        project_id=project_1.id,
        event_type=GitEventType.PUSH,
        target_branch=None,
        tracker_column_id="col-1",
    )
    dbsession.add(rule)
    await dbsession.commit()
    await dbsession.refresh(rule)

    response = await client.delete(
        f"/api/projects/{project_2.id}/rules/{rule.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Rule not found"

    # правило не должно быть удалено
    existing = await dbsession.get(AutomationRule, rule.id)
    assert existing is not None
