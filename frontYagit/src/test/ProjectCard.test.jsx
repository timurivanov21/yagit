import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { ProjectCard } from "../components/ProjectCard";

test("renders project card with name", () => {
  const projectName = `Random-${Date.now()}`;

  render(
    <ProjectCard
      projectId={1}
      name={projectName}
      onClick={vi.fn()}
      onDelete={vi.fn()}
    />,
  );

  expect(screen.getByText(projectName)).toBeInTheDocument();
});

test("calls onClick when card is clicked", async () => {
  const userEventApi = userEvent.setup();
  const onClickMock = vi.fn();
  const onDeleteMock = vi.fn();

  render(
    <ProjectCard
      projectId={1}
      name="Demo"
      onClick={onClickMock}
      onDelete={onDeleteMock}
    />,
  );

  await userEventApi.click(screen.getByTestId("project-card-1"));
  expect(onClickMock).toHaveBeenCalledTimes(1);
  expect(onDeleteMock).toHaveBeenCalledTimes(0);
});

test("calls onDelete and does not trigger onClick", async () => {
  const userEventApi = userEvent.setup();
  const onClickMock = vi.fn();
  const onDeleteMock = vi.fn();

  render(
    <ProjectCard
      projectId={1}
      name="Demo"
      onClick={onClickMock}
      onDelete={onDeleteMock}
    />,
  );

  await userEventApi.click(screen.getByTestId("project-delete-1"));
  expect(onDeleteMock).toHaveBeenCalledTimes(1);
  expect(onClickMock).toHaveBeenCalledTimes(0);
});
