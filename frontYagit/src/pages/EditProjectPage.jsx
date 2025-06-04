import { useState, useEffect  } from "react";
import { Header } from "../components/Header";
import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import GitLogo from "../assets/GitLogo.svg";
import TrackerLogo from "../assets/TrackerLogo.svg";
import TrashBin from "../assets/TrashBin.svg";

export const EditProjectPage = () => {
  const { state } = useLocation();
  const { id, name, repositories, selectedRepo } = state || {};
  const navigate = useNavigate();

  const [boards, setBoards] = useState([]);
  const [selectedBoardId, setSelectedBoardId] = useState("");
  const [columns, setColumns] = useState([]);
  const [selectedColumnId, setSelectedColumnId] = useState("");
  const apiUrl = import.meta.env.VITE_API_URL;

  const [steps, setSteps] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [newStep, setNewStep] = useState({
    gitAction: "create_branch",
    branch: "",
    trackerColumn: "",
  });


  useEffect(() => {
    const fetchBoards = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/projects/${id}/tracker_boards`);
        const data = await res.json();
        setBoards(data);
      } catch (err) {
        console.error("Ошибка при загрузке досок трекера:", err);
      }
    };

    fetchBoards();
  }, [id]);

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/projects/${id}/rules`);
        if (!res.ok) throw new Error("Ошибка при загрузке правил");

        const data = await res.json();
        const mapped = data.map((rule) => ({
          id: rule.id,
          gitAction: rule.event_type,
          branch: rule.target_branch,
          trackerBoardId: rule.tracker_board_id,
          trackerColumnId: rule.tracker_column_id,
        }));

        setSteps(mapped);
      } catch (err) {
        console.error("Ошибка при загрузке правил:", err);
      }
    };

    fetchRules();
  }, [id]);

  useEffect(() => {
    const board = boards.find((b) => b.id === Number(selectedBoardId));
    setColumns(board ? board.columns : []);
    setSelectedColumnId("");
  }, [selectedBoardId, boards]);

  const handleAddStep = async () => {
    if (!selectedColumnId || !selectedBoardId || !newStep.branch || !newStep.gitAction) {
      console.warn("Все поля должны быть заполнены");
      return;
    }

    const payload = {
      event_type: newStep.gitAction,
      target_branch: newStep.branch,
      tracker_column_id: selectedColumnId,
      tracker_board_id: Number(selectedBoardId),
      gitlab_project_id: selectedRepo.gitlab_project_id ?? 0,
    };

    try {
      const res = await fetch(`${apiUrl}/api/projects/${id}/rules/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const error = await res.text();
        console.error("Ошибка при создании правила:", error);
        return;
      }

      const result = await res.json();

      setSteps([...steps, {
        id: result.id,
        gitAction: newStep.gitAction,
        branch: newStep.branch,
        trackerBoardId: selectedBoardId,
        trackerColumnId: selectedColumnId,
      }]);

      setNewStep({ gitAction: "create_branch", branch: "", trackerColumn: "" });
      setSelectedBoardId("");
      setSelectedColumnId("");
      setShowModal(false);
    } catch (err) {
      console.error("Ошибка сети при создании правила:", err);
    }
  };

  const handleDelete = async (step) => {
    if (!step.id) return;
    try {
      const res = await fetch(`${apiUrl}/api/projects/${id}/rules/${step.id}`, {
        method: "DELETE",
      });

      if (res.status === 204) {
        setSteps((prev) => prev.filter((s) => s.id !== step.id));
      } else {
        const error = await res.text();
        console.error("Ошибка при удалении правила:", error);
      }
    } catch (err) {
      console.error("Сетевая ошибка при удалении правила:", err);
    }
  };

  return (
    <div style={styles.page}>
      <Header />
      <div style={styles.content}>
        <div style={styles.backButtonWrapper}>
          <button onClick={() => navigate("/")} style={styles.backButton}>
            ← Вернуться к проектам
          </button>
        </div>
        <h1 style={styles.title}>{name}</h1>

        <div style={styles.row}>
          <img src={GitLogo} alt="Logo" style={styles.icon}/>
          <div style={{ flex: 1 }}></div>
          <img src={TrackerLogo} alt="Logo" style={styles.icon}/>
        </div>

        {steps.map((step, index) => {
          const board = boards.find((b) => b.id === Number(step.trackerBoardId));
          const column = board?.columns.find((c) => c.id === step.trackerColumnId);
          const columnName = column ? column.name : step.trackerColumnId;

          return (
            <div key={index} style={styles.stepRow}>
              <span>{actionLabel(step.gitAction)}</span>
              <span style={styles.arrow}>→</span>
              <span>{`Перемещение в “${columnName}”`}</span>
              <button onClick={() => handleDelete(step)} style={styles.deleteButton}>
                <img src={TrashBin} alt="Logo" style={styles.icon}/>
              </button>
            </div>
          );
        })}

        <div style={styles.addWrapper}>
          <button style={styles.addButton} onClick={() => setShowModal(true)}>
          <svg width="28" height="26" viewBox="0 0 28 26" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect y="9" width="28" height="8" rx="4" fill="#D9D9D9"/>
            <rect x="10" width="8" height="26" rx="4" fill="#D9D9D9"/>
          </svg>
          </button>
        </div>
      </div>

      {showModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
          <button style={styles.closeButton} onClick={() => setShowModal(false)}>×</button>
          <div style={styles.modalRow}>
            <div style={styles.modalCol}>
              <h3 style={styles.modalTitle}>Действие в Git</h3>
              <select
                value={newStep.gitAction}
                onChange={(e) => setNewStep({ ...newStep, gitAction: e.target.value })}
                style={styles.inputBlack}
              >
                {actionOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>

              <input
                type="text"
                placeholder="Введите название ветки..."
                value={newStep.branch}
                onChange={(e) => setNewStep({ ...newStep, branch: e.target.value })}
                style={styles.inputBlack}
                className="inputBlack"
              />
            </div>

            <div style={styles.modalCol}>
            <h3 style={styles.modalTitle}>Перемещение в Tracker</h3>

          <select
            value={selectedBoardId}
            onChange={(e) => setSelectedBoardId(e.target.value)}
            style={styles.inputBlack}
          >
            <option value="">Выберите доску</option>
            {boards.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>

          <select
            value={selectedColumnId}
            onChange={(e) => setSelectedColumnId(e.target.value)}
            style={styles.inputBlack}
            disabled={!selectedBoardId}
          >
            <option value="">Выберите колонку</option>
            {columns.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
          </div>
            <button style={styles.saveButton} onClick={handleAddStep}>Добавить</button>
          </div>
        </div>
      )}
    </div>
  );
};

const actionOptions = [
  { label: "Создание ветки", value: "branch_create" },
  { label: "Пуш (коммита)", value: "push" },
  { label: "Пуш тега (создание/обновление тега)", value: "tag_push" },
  { label: "Создание merge request", value: "merge_request_opened" },
  { label: "Слияние merge request", value: "merge_request_merged" },
  { label: "Закрытие merge request без слияния", value: "merge_request_closed" },

];
const actionLabel = (value) =>
  actionOptions.find((a) => a.value === value)?.label || value;

const styles = {
  backButtonWrapper: {
    padding: "20px 0px 0 0px",
  },
  backButton: {
    backgroundColor: "#2E7CA3",
    color: "white",
    border: "none",
    borderRadius: "12px",
    padding: "10px 18px",
    fontSize: "16px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  deleteButton: {
    background: "none",
    border: "none",
    color: "white",
    fontSize: "20px",
    cursor: "pointer",
  },
  page: {
    backgroundColor: "#8DA5B4",
    height: "100vh",
    width: "100vw",
  },
  modalRow: {
    display: "flex",
    gap: "40px",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: "20px",
  },
  content: {
    padding: "20px 40px",
  },
  row: {
    display: "flex",
    alignItems: "center",
    backgroundColor: "#2E7CA3",
    borderRadius: "12px",
    padding: "12px",
    marginBottom: "20px",
    boxShadow: "2px 2px 8px rgba(0,0,0,0.2)",
  },
  title: {
    fontSize: "28px",
    fontWeight: "bold",
    marginBottom: "20px",
    color: "#2e2e2e",
  },
  stepRow: {
    backgroundColor: "#2E7CA3",
    color: "white",
    padding: "14px",
    borderRadius: "12px",
    fontWeight: "bold",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "2px 2px 8px rgba(0,0,0,0.2)",
    marginBottom: "10px",
  },
  arrow: {
    margin: "0 10px",
    fontSize: "20px",
  },
  addWrapper: {
    display: "flex",
    justifyContent: "flex-end",
    marginTop: "10px",
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
  modalOverlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0,0,0,0.3)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 1000,
  },
  modal: {
    position: "relative",
    backgroundColor: "#f0f0f0",
    padding: "30px",
    borderRadius: "30px",
    display: "flex",
    flexDirection: "column",
    boxShadow: "0 0 20px rgba(0,0,0,0.3)",
    minWidth: "600px",
    maxWidth: "90%",
  },
  modalCol: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    minWidth: "240px",
    flex: 1,
  },
  modalTitle: {
    marginBottom: "10px",
    fontSize: "18px",
    fontWeight: "bold",
    color: "#1c1c1c",
  },
  inputBlack: {
    padding: "10px",
    borderRadius: "10px",
    border: "none",
    fontSize: "14px",
    backgroundColor:  "#2E7CA3",
    color: "white",
  },
 saveButton: {
    marginTop: "20px",
    backgroundColor: "#E07A2D",
    color: "white",
    border: "none",
    borderRadius: "16px",
    padding: "12px 24px",
    fontWeight: "bold",
    fontSize: "16px",
    cursor: "pointer",
    alignSelf: "center",
    // width: "100%",
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
  saveButtonWrapper: {
    display: "flex",
    justifyContent: "center",
  },
  icon: {
    width: "32px",
    height: "32px",
    marginRight: "10px",
    borderRadius: "50%",
  },
};
