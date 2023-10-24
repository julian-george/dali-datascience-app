import { useState, useEffect } from "react";
import {
  XYPlot,
  XAxis,
  YAxis,
  HorizontalGridLines,
  LineSeries,
  DiscreteColorLegend,
} from "react-vis";

interface ITimeProfitLineProps {
  data: any[];
  height: number;
  width: number;
}

type TCategorySales = {
  [category: string]: { [monthNum: number]: number };
};

const MIN_YEAR = 2013;

const CATEGORY_COLORS: {
  [cat: string]: { title: string; color: string; strokeWidth: number };
} = {
  Furniture: {
    title: "Furniture",
    color: "orange",
    strokeWidth: 6,
  },
  Technology: { title: "Technology", color: "blue", strokeWidth: 6 },
  "Office Supplies": {
    title: "Office Supplies",
    color: "purple",
    strokeWidth: 6,
  },
};

// Returns the number of months since the beginning of the MIN_YEAR
function monthStringToNum(monthString: string) {
  const [month, day, year] = monthString.split("/");
  return (Number(year) - MIN_YEAR) * 12 + Number(month);
}

const dictNumShortenedName: { [monthNum: number]: string } = {
  1: "Jan",
  2: "Feb",
  3: "Mar",
  4: "Apr",
  5: "May",
  6: "Jun",
  7: "Jul",
  8: "Aug",
  9: "Sept",
  10: "Oct",
  11: "Nov",
  12: "Dec",
};

function monthNumToTick(monthNum: number) {
  let tickName = "";
  tickName += dictNumShortenedName[(monthNum % 12) + 1];
  tickName += " ";
  tickName += (Math.floor(monthNum / 12) + MIN_YEAR).toString().slice(2);
  return tickName;
}

const TimeQuantityLine = ({ data, width, height }: ITimeProfitLineProps) => {
  const [categorySales, setCategorySales] = useState<TCategorySales>();

  useEffect(() => {
    const newCategorySales: TCategorySales = {};
    for (const row of data) {
      const category = row["Category"];
      const purchaseDate =
        row["Order Date"] != ""
          ? row["Order Date"]
          : row["Ship Date"] != ""
          ? row["Ship Date"]
          : null;
      if (!purchaseDate || category == "") continue;
      // 1 as a fallback value
      const purchaseQuantity =
        row["Quantity"] != "" ? Number(row["Quantity"]) : 1;
      const monthNum = monthStringToNum(purchaseDate);
      if (!(category in newCategorySales)) {
        newCategorySales[category] = {};
      }
      if (monthNum in newCategorySales[category]) {
        newCategorySales[category][monthNum] += purchaseQuantity;
      } else {
        newCategorySales[category][monthNum] = purchaseQuantity;
      }
    }
    setCategorySales(newCategorySales);
  }, [data]);

  return (
    <div>
      <h2 style={{ textAlign: "center" }}>
        Quantity of Items Purchased by Month
      </h2>
      <XYPlot width={width} height={height} margin={{ left: 60 }}>
        <HorizontalGridLines />
        {categorySales &&
          Object.entries(categorySales).map(([category, quantityData]) => (
            <LineSeries
              data={Object.entries(quantityData).map(
                ([monthNum, purchaseQuantity]) => ({
                  x: Number(monthNum),
                  y: purchaseQuantity,
                })
              )}
              style={{ fill: "none", stroke: CATEGORY_COLORS[category].color }}
            />
          ))}
        <XAxis
          title="Month"
          tickFormat={(v) => monthNumToTick(v)}
          tickTotal={8}
          style={{ title: { fontSize: 24 } }}
        />
        <YAxis title="Quantity ordered" style={{ title: { fontSize: 24 } }} />
        <DiscreteColorLegend
          height={200}
          width={300}
          items={Object.values(CATEGORY_COLORS)}
        />
      </XYPlot>
    </div>
  );
};

export default TimeQuantityLine;
