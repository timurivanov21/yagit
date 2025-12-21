import { useState, useEffect } from "react";
import { ProjectCard } from "../components/ProjectCard";
import { Header } from "../components/Header";
import { useNavigate } from "react-router-dom";

export const Main = () => {
  const navigate = useNavigate();
  const apiUrl = import.meta.env.VITE_API_URL;
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await fetch(apiUrl + "/api/projects");
        if (!res.ok) throw new Error("Не удалось загрузить проекты");

        const data = await res.json();
        setProjects(data);
      } catch (err) {
        console.error("Ошибка загрузки проектов:", err);
      }
    };

    fetchProjects();
  }, []);

  const addProject = () => {
    const newId = projects.length + 1;
    setProjects([...projects, { id: newId, name: "Новый Проект" }]);
  };

  const removeProject = async (id) => {
    try {
      const res = await fetch(`${apiUrl}/api/projects/${id}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        throw new Error("Не удалось удалить проект");
      }

      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error("Ошибка при удалении проекта:", err);
    }
  };

  return (
    <div style={styles.container}>
      <Header />
      <div style={styles.inner}>
        <div style={styles.titleRow}>
          <h1 style={styles.title}>Проекты</h1>
          <button onClick={() => navigate("/create")} style={styles.addButton}>
            Добавить
          </button>
        </div>

        {projects.map((project) => (
          <ProjectCard
            key={project.id}
            name={project.name}
            onClick={() =>
              navigate("/project/edit", {
                state: {
                  id: project.id,
                  name: project.name,
                  repositories: [project],
                  selectedRepo: {
                    gitlab_project_id: project.gitlab_project_id,
                    name: project.name,
                  },
                },
              })
            }
            onDelete={() => removeProject(project.id)}
          />
        ))}
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: "#8DA5B4",
    height: "100vh",
    width: "100vw",
  },
  inner: {
    padding: "20px",
  },
  titleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    margin: 0,
    fontSize: "32px",
    fontWeight: "bold",
  },
  addButton: {
    backgroundColor: "#E07A2D",
    color: "white",
    border: "none",
    borderRadius: "16px",
    padding: "10px 20px",
    fontSize: "16px",
    cursor: "pointer",
  },
  closeButton: {
  position: "absolute",
  top: "20px",
  right: "20px",
  background: "transparent",
  border: "none",
  fontSize: "24px",
  fontWeight: "bold",
  color: "#333",
  cursor: "pointer",
},
};
