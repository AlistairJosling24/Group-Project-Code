export default function Header() {
  return (
    <header style={styles.header}>
      <h1 style={styles.logo}>AI Finance</h1>
      <span style={styles.disclaimer}>Not Financial Advice</span>
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
  disclaimer: {
    fontSize: "0.9rem",
    color: "#facc15",
  },
};
