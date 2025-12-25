import TrashBin from "../assets/TrashBin.svg";

export const ProjectCard = ({ projectId, name, onDelete, onClick }) => {
  return (
    <div
      data-testid={`project-card-${projectId}`}
      style={styles.card}
      onClick={() => onClick?.()}
    >
      <span style={styles.name}>{name}</span>

      <button
        type="button"
        data-testid={`project-delete-${projectId}`}
        aria-label={`Delete project ${name}`}
        style={styles.deleteButton}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          onDelete?.();
        }}
      >
        <img src={TrashBin} alt="Delete" style={styles.icon} />
      </button>
    </div>
  );
};

const styles = {
  card: {
    backgroundColor: "#2E7CA3",
    color: "white",
    borderRadius: "10px",
    padding: "16px",
    marginTop: "12px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "2px 2px 8px rgba(0,0,0,0.2)",
    cursor: "pointer",
  },
  name: {
    fontWeight: "bold",
  },
  deleteButton: {
    background: "none",
    border: "none",
    cursor: "pointer",
  },
  icon: {
    width: "32px",
    height: "32px",
    borderRadius: "50%",
  },
};
