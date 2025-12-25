import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Main } from "../pages/Main";

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  import.meta.env.VITE_API_URL = "http://test.local";
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("deletes project card from UI after successful DELETE", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(jsonResponse([
      { id: 1, name: "Alpha", gitlab_project_id: 101 },
      { id: 2, name: "Beta", gitlab_project_id: 102 },
    ]))
    .mockResolvedValueOnce(new Response("", { status: 204 }));

  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <Main />
    </MemoryRouter>,
  );

  await screen.findByText("Alpha");
  expect(screen.getByText("Beta")).toBeInTheDocument();

  await userEvent.click(screen.getByTestId("project-delete-1"));

  await waitFor(() => {
    expect(screen.queryByText("Alpha")).not.toBeInTheDocument();
  });
  expect(screen.getByText("Beta")).toBeInTheDocument();

  expect(fetchMock).toHaveBeenCalledWith(
    "http://test.local/api/projects/1",
    expect.objectContaining({ method: "DELETE" }),
  );
});
