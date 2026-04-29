export default function Header({ onLogout }) {
  return (
    <header style={styles.header}>
      <h1 style={styles.logo}>AI Finance</h1>

      <div style={styles.right}>
        <span style={styles.disclaimer}>Not Financial Advice</span>

        <button style={styles.logout} onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

const styles = {
  header: {
    height: "60px",
    backgroundColor: "#020617",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 25px",
    borderBottom: "1px solid #1e293b",
  },
  logo: {
    margin: 0,
    color: "#38bdf8",
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: "15px",
  },
  disclaimer: {
    fontSize: "0.9rem",
    color: "#facc15",
  },
  logout: {
    padding: "6px 12px",
    backgroundColor: "#ef4444",
    border: "none",
    borderRadius: "6px",
    color: "white",
    cursor: "pointer",
  },
};