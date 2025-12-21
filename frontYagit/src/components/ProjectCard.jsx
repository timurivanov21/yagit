import TrashBin from "../assets/TrashBin.svg";

export const ProjectCard = ({ name, onDelete, onClick }) => {
  return (
    <div style={styles.card} onClick={(e) => {
        e.stopPropagation();
        onDelete();
      }}>
      <span style={styles.name}>{name}</span>
      <button onClick={onDelete} style={styles.deleteButton}>
        <img src={TrashBin} alt="Logo" style={styles.icon}/>
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
  },
  name: {
    fontWeight: "bold",
  },
  deleteButton: {
    background: "none",
    border: "none",
    color: "white",
    fontSize: "20px",
    cursor: "pointer",
  },
};
