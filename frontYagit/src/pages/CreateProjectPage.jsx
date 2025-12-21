import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import GitLogo from "../assets/GitLogo.svg";
import TrackerLogo from "../assets/TrackerLogo.svg";

export const CreateProjectPage = () => {
  const [name, setName] = useState("");
  const [git, setGit] = useState("");
  const [tracker, setTracker] = useState("");
  const [trackerOrg, setTrackerOrg] = useState("");
  const apiUrl = import.meta.env.VITE_API_URL;

  const [createdProject, setCreatedProject] = useState(null);
  const [selectedRepo, setSelectedRepo] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async() => {
  if (!name || !git || !tracker || !trackerOrg) return;
  const payload = {
      name,
      gitlab_token: git,
      tracker_token: tracker,
      tracker_org_id: trackerOrg,
    };

    try {
      const res = await fetch(`${apiUrl}/api/projects/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const error = await res.text();
        console.error("Ошибка при создании проекта:", error);
        return;
      }

      const result = await res.json();

      setCreatedProject({
        id: result.project_id,
        name: name,
        repositories: result.repositories || [],
      });
    } catch (err) {
      console.error("Ошибка сети:", err);
    }
  };

  const handleContinue = async() => {
    if (!createdProject || !selectedRepo) return;

    const payload = {
      gitlab_project_id: selectedRepo.gitlab_project_id,
    };

    try {
      const res = await fetch(`${apiUrl}/api/projects/${createdProject.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const error = await res.text();
        console.error("Ошибка при обновлении проекта:", error);
        return;
      }


      navigate("/project/edit", {
        state: {
          id: createdProject.id,
          name: createdProject.name,
          repositories: createdProject.repositories,
          selectedRepo,
        },
      });
    } catch (err) {
      console.error("Ошибка сети при обновлении:", err);
    }
  };


  return (
    <div style={styles.container}>
    <Header />
    <div style={styles.containerLevelTwo}>
      <div style={styles.form}>
        <div style={styles.row}>
          <strong style={styles.label}>Проект</strong>
          <input
            type="text"
            placeholder="Введите название проекта..."
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.row}>
          <img src={GitLogo} alt="Logo" style={styles.icon}/>
          <input
            type="text"
            placeholder="Введите Git токен..."
            value={git}
            onChange={(e) => setGit(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.row}>
          <img src={TrackerLogo} alt="Logo" style={styles.icon}/>
          <input
            type="text"
            placeholder="Введите Tracker токен..."
            value={tracker}
            onChange={(e) => setTracker(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.row}>
          <img src={TrackerLogo} alt="Logo" style={styles.icon}/>
          <input
            type="text"
            placeholder="Введите Tracker id организации..."
            value={trackerOrg}
            onChange={(e) => setTrackerOrg(e.target.value)}
            style={styles.input}
          />
        </div>

        <button style={styles.addButton} onClick={handleSubmit}>
          Выбрать проект
        </button>

        {createdProject && (
        <div>
        <div style={styles.row}>
          <select
              value={selectedRepo?.gitlab_project_id || ""}
              onChange={(e) => {
                const id = Number(e.target.value);
                const selected = createdProject.repositories.find(r => r.gitlab_project_id === id);
                setSelectedRepo(selected); //
              }}
            style={styles.input}
          >
            <option value="" disabled>Выберите репозиторий...</option>
            {createdProject.repositories.map((repo) => (
              <option key={repo.gitlab_project_id} value={repo.gitlab_project_id}>
                {repo.name}
              </option>
            ))}
          </select>
          </div>

          <div style={{  display: "flex", justifyContent: "center"}}>
          <button
            style={styles.createButton}
            onClick={handleContinue}
            disabled={!selectedRepo}
          >
            Далее
          </button>
          </div>
        </div>
      )}
      </div>
    </div>
    </div>
  );
};

const styles = {
  createButton: {
    marginTop: 20,
    backgroundColor: "#E07A2D",
    color: "white",
    border: "none",
    borderRadius: "16px",
    padding: "12px 20px",
    fontSize: "18px",
    cursor: "pointer",
    alignSelf: "center",
  },
  container: {
    backgroundColor: "#8DA5B4",
    height: "100vh",
    width: "100vw",
  },
  containerLevelTwo: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
    width: "50%",
  },
  row: {
    display: "flex",
    alignItems: "center",
    backgroundColor: "#2E7CA3",
    borderRadius: "10px",
    padding: "10px 15px",
    boxShadow: "2px 2px 8px rgba(0,0,0,0.3)",
  },
  label: {
    color: "white",
    fontSize: "20px",
    marginRight: "10px",
  },
  icon: {
    width: "32px",
    height: "32px",
    marginRight: "10px",
    borderRadius: "50%",
  },
  input: {
    flex: 1,
    padding: "10px",
    fontSize: "16px",
    borderRadius: "10px",
    border: "none",
    outline: "none",
    backgroundColor: "white",
    color: "black",
  },
  addButton: {
    backgroundColor: "#E07A2D",
    color: "white",
    border: "none",
    borderRadius: "16px",
    padding: "12px 20px",
    fontSize: "18px",
    cursor: "pointer",
    alignSelf: "center",
  },
};
