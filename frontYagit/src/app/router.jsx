import { createBrowserRouter, RouterProvider } from "react-router-dom";
import {Main} from "../pages/Main";
import {CreateProjectPage} from "../pages/CreateProjectPage";
import {EditProjectPage} from "../pages/EditProjectPage";

const router = createBrowserRouter([
  { path: "/", element: <Main /> },
  { path: "/create", element: <CreateProjectPage /> },
  { path: "/project/edit", element: <EditProjectPage /> },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
