import { useState } from "react";

export default function Simulator({ market, data }) {
  const [amount, setAmount] = useState("");

  if (!data) return null;

  const currentPrice = data.historical[data.historical.length - 1];
  const predictedPrice = data.predicted;

  const investment = parseFloat(amount);

  let shares = 0;
  let futureValue = 0;
  let profit = 0;

  if (investment > 0) {
    shares = investment / currentPrice;
    futureValue = shares * predictedPrice;
    profit = futureValue - investment;
  }

  return (
    <div style={styles.container}>
      <h3>💸 Investment Simulator</h3>

      <input
        type="number"
        placeholder="Enter amount ($)"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        style={styles.input}
      />

      {investment > 0 && (
        <div style={styles.results}>
          <p>Shares: {shares.toFixed(4)}</p>
          <p>Future Value: ${futureValue.toFixed(2)}</p>

          <p style={{
            color: profit >= 0 ? "#22c55e" : "#ef4444"
          }}>
            Profit: ${profit.toFixed(2)}
          </p>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    marginTop: "20px",
    padding: "15px",
    backgroundColor: "#020617",
    border: "1px solid #1e293b",
    borderRadius: "10px"
  },
  input: {
    padding: "8px",
    width: "100%",
    marginTop: "10px",
    marginBottom: "10px"
  },
  results: {
    marginTop: "10px",
    color: "#94a3b8"
  }
};