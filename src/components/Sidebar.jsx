export default function Sidebar({ market, setMarket }) {
  const markets = ["AAPL", "MSFT", "TSLA"];

  return (
    <aside style={styles.sidebar}>
      <h2>Markets</h2>
      <ul style={styles.list}>
        {markets.map((m) => (
          <li
            key={m}
            onClick={() => setMarket(m)}
            style={{
              ...styles.item,
              ...(market === m ? styles.active : {}),
            }}
          >
            {m}
          </li>
        ))}
      </ul>
    </aside>
  );
}

const styles = {
  sidebar: { backgroundColor: "#020617", padding: "20px", borderRight: "1px solid #1e293b" },
  list: { listStyle: "none", padding: 0 },
  item: { padding: "8px 0", cursor: "pointer", color: "#94a3b8" },
  active: { color: "#38bdf8", fontWeight: "bold" },
};