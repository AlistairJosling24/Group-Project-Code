import { useState } from "react";
import Header from "./components/header";
import Sidebar from "./components/Sidebar";
import ChartPanel from "./components/ChartPanel";
import DecisionPanel from "./components/DecisionPanel";
import marketData from "./marketData.json";
import Login from "./pages/login";

export default function App() {

  const [loggedIn, setLoggedIn] = useState(false);
  const [market, setMarket] = useState("AAPL");

  const selectedData = marketData[market];

  if (!loggedIn) {
    return <Login setLoggedIn={setLoggedIn} />;
  }

  return (
    <>
      <Header />
      <div className="container">
        <Sidebar market={market} setMarket={setMarket} />
        <ChartPanel market={market} data={selectedData} />
        <DecisionPanel market={market} data={selectedData} />
      </div>
    </>
  );
}