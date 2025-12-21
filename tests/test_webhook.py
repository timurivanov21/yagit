import pytest
from pytest_mock import MockerFixture
from starlette import status

from yagit.db.models.automation_rule import GitEventType, AutomationRule
from yagit.db.models.project import Project


@pytest.mark.anyio
async def test_gitlab_webhook_missing_token(
    client,
):
    response = await client.post("/api/webhook/gitlab", json={})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Missing X-Gitlab-Token"


@pytest.mark.anyio
async def test_gitlab_webhook_invalid_token(
    client,
    dbsession,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="valid-secret",
    )
    dbsession.add(project)
    await dbsession.commit()

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "invalid-secret"},
        json={},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid secret token"


@pytest.mark.anyio
async def test_gitlab_webhook_skipped_event(
    client,
    dbsession,
    mocker: MockerFixture,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(None, None, None),
    )

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json={"any": "payload"},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"skipped": True}


@pytest.mark.anyio
async def test_gitlab_webhook_no_issue_key(
    client,
    dbsession,
    mocker,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.PUSH,
            None,
            "",  # issue_key пустой
        ),
    )

    tracker_mock = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json={"commits": []},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        "matched": 0,
    }

    tracker_mock.assert_not_called()


@pytest.mark.anyio
async def test_gitlab_webhook_no_matching_rules(
    client,
    dbsession,
    mocker,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.PUSH,
            None,
            "PROJ-1",
        ),
    )

    tracker_mock = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json={"commits": []},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"matched": 0}

    tracker_mock.assert_not_called()


@pytest.mark.anyio
async def test_gitlab_webhook_push_single_rule(
    client,
    dbsession,
    mocker: MockerFixture,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    rule = AutomationRule(
        project_id=project.id,
        event_type=GitEventType.PUSH,
        target_branch=None,
        tracker_column_id="IN_PROGRESS",
    )
    dbsession.add(rule)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.PUSH,
            None,
            "PROJ-1",
        ),
    )

    tracker_cls = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )

    tracker_instance = tracker_cls.return_value.__aenter__.return_value
    tracker_instance.move_issue = mocker.AsyncMock()
    tracker_instance.add_comment = mocker.AsyncMock()

    payload = {
        "commits": [
            {"url": "http://commit/1"},
            {"url": "http://commit/2"},
        ]
    }

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json=payload,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"accepted": 1}

    tracker_instance.move_issue.assert_awaited_once_with(
        "PROJ-1",
        "IN_PROGRESS",
    )

    tracker_instance.add_comment.assert_awaited_once_with(
        "PROJ-1",
        "http://commit/1\nhttp://commit/2",
    )


@pytest.mark.anyio
async def test_gitlab_webhook_push_multiple_rules(
    client,
    dbsession,
    mocker: MockerFixture,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    rules = [
        AutomationRule(
            project_id=project.id,
            event_type=GitEventType.PUSH,
            target_branch=None,
            tracker_column_id="COL_1",
        ),
        AutomationRule(
            project_id=project.id,
            event_type=GitEventType.PUSH,
            target_branch=None,
            tracker_column_id="COL_2",
        ),
    ]
    dbsession.add_all(rules)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.PUSH,
            None,
            "PROJ-2",
        ),
    )

    tracker_cls = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )
    tracker_instance = tracker_cls.return_value.__aenter__.return_value
    tracker_instance.move_issue = mocker.AsyncMock()
    tracker_instance.add_comment = mocker.AsyncMock()

    payload = {
        "commits": [{"url": "http://commit/1"}],
    }

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json=payload,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"accepted": 2}

    assert tracker_instance.move_issue.await_count == 2
    assert tracker_instance.add_comment.await_count == 2


@pytest.mark.anyio
async def test_gitlab_webhook_mr_exact_branch_match(
    client,
    dbsession,
    mocker: MockerFixture,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    rule = AutomationRule(
        project_id=project.id,
        event_type=GitEventType.MERGE_REQUEST_OPENED,
        target_branch="main",
        tracker_column_id="MR_MAIN",
    )
    dbsession.add(rule)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.MERGE_REQUEST_OPENED,
            "main",
            "PROJ-10",
        ),
    )

    tracker_cls = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )
    tracker = tracker_cls.return_value.__aenter__.return_value
    tracker.move_issue = mocker.AsyncMock()
    tracker.add_comment = mocker.AsyncMock()

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json={},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"accepted": 1}

    tracker.move_issue.assert_awaited_once_with(
        "PROJ-10",
        "MR_MAIN",
    )

    tracker.add_comment.assert_not_awaited()


@pytest.mark.anyio
async def test_gitlab_webhook_mr_null_branch_fallback(
    client,
    dbsession,
    mocker: MockerFixture,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    rule = AutomationRule(
        project_id=project.id,
        event_type=GitEventType.MERGE_REQUEST_MERGED,
        target_branch=None,  # fallback
        tracker_column_id="MR_ANY",
    )
    dbsession.add(rule)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.MERGE_REQUEST_MERGED,
            "develop",  # ветка не совпадает, но rule.target_branch is NULL
            "PROJ-20",
        ),
    )

    tracker_cls = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )
    tracker = tracker_cls.return_value.__aenter__.return_value
    tracker.move_issue = mocker.AsyncMock()
    tracker.add_comment = mocker.AsyncMock()

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json={},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"accepted": 1}

    tracker.move_issue.assert_awaited_once_with(
        "PROJ-20",
        "MR_ANY",
    )
    tracker.add_comment.assert_not_awaited()


@pytest.mark.anyio
async def test_gitlab_webhook_mr_multiple_rules(
    client,
    dbsession,
    mocker: MockerFixture,
):
    project = Project(
        name="Project",
        gitlab_token="gitlab-token",
        tracker_token="tracker-token",
        tracker_org_id="org-id",
        gitlab_webhook_secret="secret",
    )
    dbsession.add(project)
    await dbsession.commit()
    await dbsession.refresh(project)

    rules = [
        AutomationRule(
            project_id=project.id,
            event_type=GitEventType.MERGE_REQUEST_CLOSED,
            target_branch="main",
            tracker_column_id="MR_MAIN",
        ),
        AutomationRule(
            project_id=project.id,
            event_type=GitEventType.MERGE_REQUEST_CLOSED,
            target_branch=None,
            tracker_column_id="MR_ANY",
        ),
    ]
    dbsession.add_all(rules)
    await dbsession.commit()

    mocker.patch(
        "yagit.web.api.webhook.views._parse_event_type",
        return_value=(
            GitEventType.MERGE_REQUEST_CLOSED,
            "main",
            "PROJ-30",
        ),
    )

    tracker_cls = mocker.patch(
        "yagit.web.api.webhook.views.TrackerClient",
        autospec=True,
    )
    tracker = tracker_cls.return_value.__aenter__.return_value
    tracker.move_issue = mocker.AsyncMock()
    tracker.add_comment = mocker.AsyncMock()

    response = await client.post(
        "/api/webhook/gitlab",
        headers={"X-Gitlab-Token": "secret"},
        json={},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"accepted": 2}

    assert tracker.move_issue.await_count == 2
    tracker.add_comment.assert_not_awaited()
