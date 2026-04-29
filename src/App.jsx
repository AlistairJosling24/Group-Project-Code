import { useState, useEffect } from "react";
import axios from "axios";

import Header from "./components/header";
import Sidebar from "./components/Sidebar";
import ChartPanel from "./components/ChartPanel";
import DecisionPanel from "./components/DecisionPanel";
import Login from "./pages/login";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [market, setMarket] = useState("AAPL");
  const [marketData, setMarketData] = useState(null);

  // 🔥 Check login from localStorage on load
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setLoggedIn(true);
    }
  }, []);

  // 🔥 Fetch data ONLY if logged in
  useEffect(() => {
    if (!loggedIn) return;

    const fetchData = async () => {
      try {
        const res = await axios.get("http://localhost:5000/api/market-data");
        setMarketData(res.data);
      } catch (err) {
        console.error("API ERROR:", err);
      }
    };

    fetchData();
  }, [loggedIn]);

  // 🔥 Logout function
  const handleLogout = () => {
    localStorage.removeItem("token");
    setLoggedIn(false);
    setMarketData(null);
  };

  // 🔒 Show login if not logged in
  if (!loggedIn) {
    return <Login setLoggedIn={setLoggedIn} />;
  }

  if (!marketData) {
    return <div style={{ padding: "20px" }}>Loading market data...</div>;
  }

  const selectedData = marketData[market];

  return (
    <>
      <Header onLogout={handleLogout} />
      <div className="container">
        <Sidebar market={market} setMarket={setMarket} />
        <ChartPanel market={market} data={selectedData} />
        <DecisionPanel market={market} data={selectedData} />
      </div>
    </>
  );
}