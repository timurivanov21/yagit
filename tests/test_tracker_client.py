from unittest.mock import AsyncMock

import httpx
import pytest

from yagit.services.tracker import (
    IssueNotFound,
    TrackerClient,
    TrackerError,
    TransitionNotFound,
)

FIND_TRANSITION_CASES = [
    pytest.param(
        [
            {"id": "t1", "to": {"id": "inProgress", "key": "IN_PROGRESS"}},
            {"id": "t2", "to": {"id": "done", "key": "DONE"}},
        ],
        "inProgress",
        "t1",
        id="match-by-status-id",
    ),
    pytest.param(
        [
            {"id": "t1", "to": {"id": "inProgress", "key": "IN_PROGRESS"}},
            {"id": "t2", "to": {"id": "done", "key": "DONE"}},
        ],
        "DONE",
        "t2",
        id="match-by-status-key",
    ),
]


def _make_response(
    status_code: int,
    url: str = "https://api.tracker.yandex.net/v3/boards",
    text: str = "oops",
):
    """
    httpx.Response желательно создавать с Request, чтобы .text / .json работали предсказуемо.
    """
    req = httpx.Request("GET", url)
    return httpx.Response(status_code=status_code, request=req, text=text)


@pytest.mark.anyio
async def test_request_requires_context_manager():
    client = TrackerClient(token="t", org_id="org")
    with pytest.raises(AssertionError, match="Use inside `async with TrackerClient`"):
        await client._request("GET", "/v3/boards")


@pytest.mark.anyio
async def test_request_success_no_retries(mocker):
    tr = TrackerClient(token="t", org_id="org")
    tr._client = mocker.Mock(spec=httpx.AsyncClient)
    tr._client.request = AsyncMock(return_value=_make_response(200, text="ok"))

    sleep_mock = mocker.patch("asyncio.sleep", new=AsyncMock())

    resp = await tr._request("GET", "/v3/boards")

    assert resp.status_code == 200
    tr._client.request.assert_awaited_once_with("GET", "/v3/boards")
    sleep_mock.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "statuses, expected_sleeps",
    [
        # 1 retry: first 429 -> second 200, sleep called once with 0.4*1
        ([429, 200], [0.4]),
        # 2 retries: 503 -> 503 -> 200, sleeps: 0.4*1, 0.4*2
        ([503, 503, 200], [0.4, 0.8]),
    ],
)
async def test_request_retries_with_backoff(mocker, statuses, expected_sleeps):
    tr = TrackerClient(token="t", org_id="org")
    tr._client = mocker.Mock(spec=httpx.AsyncClient)
    tr._client.request = AsyncMock(side_effect=[_make_response(s) for s in statuses])

    sleep_mock = mocker.patch("asyncio.sleep", new=AsyncMock())

    resp = await tr._request("GET", "/v3/boards")

    assert resp.status_code == 200
    assert tr._client.request.await_count == len(statuses)

    # проверяем, что sleep вызвался нужное число раз и с нужными аргументами
    assert sleep_mock.await_count == len(expected_sleeps)
    actual = [call.args[0] for call in sleep_mock.await_args_list]
    assert actual == expected_sleeps


@pytest.mark.anyio
async def test_request_404_raises_issue_not_found(mocker):
    tr = TrackerClient(token="t", org_id="org")
    tr._client = mocker.Mock(spec=httpx.AsyncClient)
    tr._client.request = AsyncMock(return_value=_make_response(404, text="not found"))

    # важно: sleep не нужен, но пусть будет на всякий
    mocker.patch("asyncio.sleep", new=AsyncMock())

    with pytest.raises(IssueNotFound) as exc:
        await tr._request("GET", "/v3/issues/ABC-1")

    # IssueNotFound(url) — url здесь именно тот, что мы передали в _request
    assert "/v3/issues/ABC-1" in str(exc.value)


@pytest.mark.anyio
@pytest.mark.parametrize("status_code", [400, 401, 403, 422, 500])
async def test_request_http_error_raises_tracker_error(mocker, status_code):
    tr = TrackerClient(token="t", org_id="org")
    tr._client = mocker.Mock(spec=httpx.AsyncClient)
    tr._client.request = AsyncMock(return_value=_make_response(status_code, text="bad"))

    mocker.patch("asyncio.sleep", new=AsyncMock())

    with pytest.raises(TrackerError) as exc:
        await tr._request("GET", "/v3/boards")

    assert str(status_code) in str(exc.value)
    assert "bad" in str(exc.value)


@pytest.mark.anyio
async def test_request_exhausts_retries_then_raises_tracker_error(mocker):
    """
    Если все попытки вернули retry-статус, цикл закончится и дальше будет TrackerError (>=400).
    """
    tr = TrackerClient(token="t", org_id="org")
    tr._client = mocker.Mock(spec=httpx.AsyncClient)

    # _MAX_RETRIES = 3, пусть все 3 попытки будут 503
    tr._client.request = AsyncMock(side_effect=[_make_response(503, text="retry")] * 3)

    sleep_mock = mocker.patch("asyncio.sleep", new=AsyncMock())

    with pytest.raises(TrackerError) as exc:
        await tr._request("GET", "/v3/boards")

    assert "503" in str(exc.value)
    assert "retry" in str(exc.value)

    assert tr._client.request.await_count == 3
    # sleep будет вызван после 1-й и 2-й и 3-й попытки (по текущей реализации — да, даже после последней)
    # ожидаем: 0.4, 0.8, 1.2
    actual = [call.args[0] for call in sleep_mock.await_args_list]
    for item in actual:
        assert float(f"{item:.2f}") in [0.4, 0.8, 1.2]


@pytest.mark.parametrize(
    "transitions, target_status, expected_id",
    FIND_TRANSITION_CASES,
)
def test_find_transition_id_success(transitions, target_status, expected_id):
    transition_id = TrackerClient._find_transition_id(
        transitions,
        target_status,
    )

    assert transition_id == expected_id


def test_find_transition_id_not_found():
    transitions = [
        {"id": "t1", "to": {"id": "todo", "key": "TODO"}},
    ]

    with pytest.raises(TransitionNotFound) as exc:
        TrackerClient._find_transition_id(transitions, "done")

    assert "done" in str(exc.value)


@pytest.mark.anyio
async def test_list_boards(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"id": 1}, {"id": 2}]

    mocker.patch.object(
        tr,
        "_request",
        AsyncMock(return_value=mock_response),
    )

    result = await tr.list_boards()

    tr._request.assert_awaited_once_with("GET", "/v3/boards")
    assert result == [{"id": 1}, {"id": 2}]


@pytest.mark.anyio
async def test_list_columns(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"id": "c1"}, {"id": "c2"}]

    mocker.patch.object(
        tr,
        "_request",
        AsyncMock(return_value=mock_response),
    )

    result = await tr.list_columns(board_id="board-1")

    tr._request.assert_awaited_once_with(
        "GET",
        "/v3/boards/board-1/columns",
    )
    assert result == [{"id": "c1"}, {"id": "c2"}]


@pytest.mark.anyio
async def test_add_comment(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mocker.patch.object(
        tr,
        "_request",
        AsyncMock(return_value=None),
    )

    await tr.add_comment("PROJ-1", "Hello world")

    tr._request.assert_awaited_once_with(
        "POST",
        "/v3/issues/PROJ-1/comments",
        json={"text": "Hello world"},
    )


@pytest.mark.anyio
async def test_move_issue_success(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mocker.patch.object(
        tr,
        "_get_transitions",
        AsyncMock(
            return_value=[
                {
                    "id": "tr-1",
                    "to": {"id": "inProgress", "key": "IN_PROGRESS"},
                },
            ],
        ),
    )

    mocker.patch.object(
        tr,
        "_find_transition_id",
        return_value="tr-1",
    )

    mocker.patch.object(
        tr,
        "_request",
        AsyncMock(return_value=None),
    )

    await tr.move_issue("PROJ-1", "inProgress")

    tr._get_transitions.assert_awaited_once_with("PROJ-1")
    tr._find_transition_id.assert_called_once()
    tr._request.assert_awaited_once_with(
        "POST",
        "/v3/issues/PROJ-1/transitions/tr-1/_execute",
    )


@pytest.mark.anyio
async def test_move_issue_transition_not_found(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mocker.patch.object(
        tr,
        "_get_transitions",
        AsyncMock(
            return_value=[
                {
                    "id": "tr-1",
                    "to": {"id": "todo", "key": "TODO"},
                },
            ],
        ),
    )

    # _request не должен вызываться
    mocker.patch.object(tr, "_request", AsyncMock())

    with pytest.raises(TransitionNotFound):
        await tr.move_issue("PROJ-1", "done")

    tr._request.assert_not_awaited()


@pytest.mark.anyio
async def test_move_issue_issue_not_found(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mocker.patch.object(
        tr,
        "_get_transitions",
        AsyncMock(side_effect=IssueNotFound("PROJ-404")),
    )

    mocker.patch.object(tr, "_request", AsyncMock())

    with pytest.raises(IssueNotFound):
        await tr.move_issue("PROJ-404", "done")

    tr._request.assert_not_awaited()


@pytest.mark.anyio
async def test_move_issue_execute_raises_tracker_error(mocker):
    tr = TrackerClient(token="t", org_id="org")

    mocker.patch.object(
        tr,
        "_get_transitions",
        AsyncMock(
            return_value=[
                {
                    "id": "tr-1",
                    "to": {"id": "done", "key": "DONE"},
                },
            ],
        ),
    )

    mocker.patch.object(
        tr,
        "_request",
        AsyncMock(side_effect=TrackerError("500: error")),
    )

    with pytest.raises(TrackerError):
        await tr.move_issue("PROJ-1", "done")
