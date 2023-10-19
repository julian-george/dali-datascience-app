import React, { useState, useEffect } from "react";
import "./App.css";
import CategoryProfitBar from "./components/CategoryProfitBar";
import LocationQuantityMap from "./components/LocationQuantityMap";
import TimeProfitLine from "./components/TimeProfitLine";
import { csv } from "d3";

const DATA_URL =
  "https://raw.githubusercontent.com/dali-lab/dali-challenges/main/data/Sample%20-%20Superstore.csv";

const App = () => {
  const [data, setData] = useState<any[] | null>(null);
  useEffect(() => {
    csv(DATA_URL).then((res) => {
      setData(res);
    });
  }, []);
  return (
    <div className="App">
      {data ? (
        <div>
          <CategoryProfitBar data={data} height={640} width={1080} />
          <LocationQuantityMap />
          <TimeProfitLine />
        </div>
      ) : (
        "Loading..."
      )}
    </div>
  );
};

export default App;
