import {
  Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend);

export default function ChartPanel({ market, data }) {
  if (!data) return <main style={{padding: "20px"}}>Loading AI Data...</main>;

  const chartData = {
    labels: [...data.labels, "Prediction"],
    datasets: [
      {
        label: "Historical Price",
        data: [...data.historical, null],
        borderColor: "#38bdf8",
        tension: 0.3,
      },
      {
        label: "AI Forecast",
        data: [
          ...Array(data.historical.length - 1).fill(null),
          data.historical[data.historical.length - 1], // Connects to last actual price
          data.predicted,
        ],
        borderColor: data.signal === "BUY" ? "#22c55e" : "#ef4444",
        borderDash: [5, 5],
        pointRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    scales: {
      x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
      y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
    },
    plugins: { legend: { labels: { color: "#e5e7eb" } } }
  };

  return (
    <main style={{ padding: "20px", backgroundColor: "#0f172a", flex: 1 }}>
      <h2>{market} / USD</h2>
      <Line data={chartData} options={options} />
      <div style={{marginTop: '20px', color: '#94a3b8'}}>
         <p>Sentiment Score: {data.sentiment}</p>
      </div>
    </main>
  );
}
