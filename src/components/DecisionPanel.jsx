export default function DecisionPanel({ market, data }) {
  if (!data) return <aside style={styles.panel}>Calculating...</aside>;

  const isBuy = data.signal === "BUY";
  const isSell = data.signal === "SELL";

  return (
    <aside style={styles.panel}>
      <h2>AI Recommendation</h2>
      <div style={{
        ...styles.signal,
        backgroundColor: isBuy ? "#14532d" : isSell ? "#450a0a" : "#1e293b",
        color: isBuy ? "#22c55e" : isSell ? "#ef4444" : "#94a3b8"
      }}>
        {data.signal}
      </div>
      <p><strong>Confidence:</strong> {data.confidence}%</p>
      <p><strong>Sentiment:</strong> {data.sentiment}</p>
      <p style={styles.text}>
        Based on the latest technical and news data, the AI model has a {data.confidence}% 
        probability for the next price movement.
      </p>
    </aside>
  );
}

const styles = {
  panel: { backgroundColor: "#020617", padding: "20px", borderLeft: "1px solid #1e293b" },
  signal: { textAlign: "center", padding: "15px", fontSize: "1.5rem", fontWeight: "bold", marginBottom: "15px", borderRadius: "8px" },
  text: { fontSize: "0.9rem", color: "#cbd5f5", lineHeight: "1.4" },
};
