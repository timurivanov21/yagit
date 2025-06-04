import YaGitLogo from "../assets/YaGitLogo.svg";
import { useNavigate } from "react-router-dom";

export const Header = () => {
 const navigate = useNavigate();

  return (
    <div style={styles.header}>
      <img src={YaGitLogo} alt="Logo" onClick={() => navigate("/")}/>
      <div style={styles.spacer}></div>
    </div>
  );
};

const styles = {
  header: {
    backgroundColor: "#1C3848",
    display: "flex",
    alignItems: "center",
    padding: "10px 20px",
  },
  logo: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
  },
  spacer: {
    flexGrow: 1,
  },
};
