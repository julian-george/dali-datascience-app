import React, { useState, useEffect } from "react";
import logo from "./logo.svg";
import "./App.css";
import { csv } from "d3";

function App() {
  const [data, setData] = useState<any[] | null>(null);
  useEffect(() => {
    csv(
      "https://raw.githubusercontent.com/dali-lab/dali-challenges/main/data/Dartmouth%20-%20Courses.csv"
    ).then((res) => {
      setData(res);
    });
  }, []);
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.tsx</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
