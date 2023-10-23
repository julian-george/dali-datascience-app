import { useEffect, useState, useRef, useCallback } from "react";
import * as d3 from "d3";
import "../App.css";

interface ICategoryProfitBarProps {
  data: any[];
  height: number;
  width: number;
}

type TCategoryDatum = {
  mean: number;
  sampleSize: number;
};

type TCategoryData = { [category: string]: TCategoryDatum };

type TSubcategoryData = {
  [category: string]: { [subcategory: string]: TCategoryDatum };
};

type TCategoryLists = {
  [category: string]: number[];
};

type TSubcategoryLists = {
  [category: string]: {
    [subcategory: string]: number[];
  };
};

type TBarDatum = {
  category: string;
  mean: number;
};

type TRenderData = {
  categoryList: string[];
  xScaler: d3.ScaleBand<string>;
  yScaler: d3.ScaleLinear<number, number, never>;
  graphMax: number;
  graphMin: number;
  minMean: number;
  maxMean: number;
};

const GRAPH_MARGIN_LEFT = 108;
const GRAPH_MARGIN_BOTTOM = 32;
const GRAPH_MARGIN_TOP = 0;
const LABEL_BAR_PADDING = 8;

// Rounds numbers and properly appends dollar sign to negative numbers
function numToDollars(num: number): string {
  let dollarString = "";
  num = Math.round(num * 100) / 100;
  // If the num is negative, we want the "-" before the "$"
  if (Math.sign(num) === -1) {
    dollarString += "-";
    num *= -1;
  }
  dollarString += "$";
  dollarString += num.toString();
  return dollarString;
}

const CategoryProfitBar = (props: ICategoryProfitBarProps) => {
  const { data, height, width } = props;
  const [categoryData, setCategoryData] = useState<TCategoryData>({});
  const [renderData, setRenderData] = useState<TRenderData | null>(null);
  const [subcategoryData, setSubcategoryData] = useState<TSubcategoryData>({});
  const [selectedData, setSelectedData] = useState<TBarDatum[]>([]);
  const [currentCategory, setCategory] = useState<string | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);

  const changeSelectedData = useCallback(
    (category?: string) => {
      const selectedCategories = category
        ? subcategoryData[category]
        : categoryData;
      const newSelectedData = Object.entries(selectedCategories).map(
        ([category, datum]) => ({ category: category, mean: datum.mean })
      );
      setSelectedData(newSelectedData);
      const svgElement = d3.select(svgRef.current);
      if (category) {
        svgElement
          .append("text")
          .attr("x", GRAPH_MARGIN_LEFT)
          .attr("y", height - 16)
          .attr("fill", "currentColor")
          .attr("text-anchor", "start")
          .attr("class", "back-text")
          .style("cursor", "pointer")
          .style("font-weight", "bold")
          .style("font-size", "10px")
          .text("← Back")
          .on("click", () => {
            changeSelectedData();
          });
      } else {
        svgElement.selectAll(".back-text").remove();
      }
      setCategory(category || null);
    },
    [subcategoryData, categoryData, setSelectedData, svgRef, height]
  );

  useEffect(() => {
    const categoryProfitLists: TCategoryLists = {};
    const subcategoryProfitLists: TSubcategoryLists = {};
    // First, we go through the data, row by row,
    //   and add each datum's profit to a list corresponding to that datum's category and subcategory
    for (const row of data) {
      const category = row["Category"];
      // For our purposes, we just discard rows with no given category

      const subcategory = row["Sub-Category"];
      if (category === "") continue;
      if (!(category in categoryProfitLists)) {
        categoryProfitLists[category] = [];
        subcategoryProfitLists[category] = {};
      }
      const profit = Number(row["Profit"]);
      categoryProfitLists[category].push(profit);

      // Skip the subcategory processing if it's blank

      if (subcategory === "") continue;
      if (!(subcategory in subcategoryProfitLists[category])) {
        subcategoryProfitLists[category][subcategory] = [];
      }
      subcategoryProfitLists[category][subcategory].push(profit);
    }
    // Once we've assembled these lists, we take their means and add them to the category/subcategory data
    for (const [category, categoryProfits] of Object.entries(
      categoryProfitLists
    )) {
      const meanCategoryProfit = d3.mean(categoryProfits) || 0;
      // forgive the ugly object assignment: this is just adding a TCategoryDatum to the state for this category
      setCategoryData((prev) => ({
        ...prev,
        [category]: {
          mean: meanCategoryProfit,
          sampleSize: categoryProfits.length,
        },
      }));
      setSubcategoryData((prev) => ({ ...prev, [category]: {} }));
      for (const [subcategory, subcategoryProfits] of Object.entries(
        subcategoryProfitLists[category]
      )) {
        const meanSubcategoryProfit = d3.mean(subcategoryProfits) || 0;
        // adding a TCategoryDatum to the state for the subcategory nested inside the category
        setSubcategoryData((prev) => ({
          ...prev,
          [category]: {
            ...prev[category],
            ...{
              [subcategory]: {
                mean: meanSubcategoryProfit,
                sampleSize: subcategoryProfits.length,
              },
            },
          },
        }));
      }
    }
    changeSelectedData();
  }, [data]);

  useEffect(() => {
    const categoryList = selectedData.map((datum) => datum.category);
    const xScaler = d3
      .scaleBand()
      .domain(categoryList)
      .range([GRAPH_MARGIN_LEFT, width])
      .padding(0.1);
    const means = Object.values(selectedData).map((datum) => datum.mean);
    const maxMean = d3.max(means) || 0;
    const graphMax = maxMean * 1.5;
    const minMean = d3.min(means) || 0;
    const graphMin = minMean >= 0 ? 0 : minMean * 1.5;
    const yScaler = d3
      .scaleLinear()
      .domain([graphMin, graphMax])
      .range([height - GRAPH_MARGIN_BOTTOM, GRAPH_MARGIN_TOP]);
    setRenderData({
      categoryList,
      xScaler,
      yScaler,
      graphMax,
      graphMin,
      minMean,
      maxMean,
    });
  }, [height, width, selectedData]);

  // Using refs here may be hacky, but it's better (imo) than working directly w/ SVGs like this recommends:
  //   https://2019.wattenberger.com/blog/react-and-d3
  useEffect(() => {
    if (!renderData) return;
    const svgElement = d3.select(svgRef.current);
    // Clears previously rendered axes
    svgElement.selectAll(".axis").remove();
    // Rerender bottom axis
    svgElement
      .append("g")
      .call(d3.axisBottom(renderData.xScaler))
      .attr("transform", `translate(0,${height - GRAPH_MARGIN_BOTTOM})`)
      .attr("class", "axis x-axis");
    // Rerender left (vertical) axis
    svgElement
      .append("g")
      .call(d3.axisLeft(renderData.yScaler))
      .call((g) =>
        g
          .append("text")
          .attr("x", -1 * GRAPH_MARGIN_LEFT + 4)
          .attr(
            "y",
            renderData.yScaler((renderData.graphMax + renderData.graphMin) / 2)
          )
          .attr("fill", "currentColor")
          .attr("text-anchor", "start")
          .attr("font-size", 12)
          .text("Mean Profit ($)")
      )
      .attr("transform", `translate(${GRAPH_MARGIN_LEFT},0)`)
      .attr("class", "axis");

    // If there are negative means, display zero line
    if (renderData.minMean < 0) {
      svgElement
        .append("line")
        .style("stroke", "black")
        .style("stroke-width", 1)
        .attr("class", "zero-line")
        .attr("x1", GRAPH_MARGIN_LEFT)
        .attr("y1", renderData.yScaler(0))
        .attr("x2", width)
        .attr("y2", renderData.yScaler(0));
    } else {
      svgElement.selectAll(".zero-line").remove();
    }

    // If there's no "currentCategory" (if we're displaying a subcategory), display the back button
    if (!currentCategory) {
      svgElement
        .selectAll(".x-axis .tick")
        .style("font-weight", "bold")
        .style("cursor", "pointer");
      svgElement.selectAll(".x-axis .tick").on("click", (d) => {
        const categoryName = d.target.innerHTML;
        changeSelectedData(categoryName);
      });
    }
    svgElement
      .selectAll("rect")
      .transition()
      .duration(100)
      .ease(d3.easeLinear)
      .style("opacity", 1);
  }, [svgRef, renderData, changeSelectedData, currentCategory, height, width]);
  return (
    <div style={{ width, height }}>
      <h2 style={{ textAlign: "center" }}>
        Average Profit by Product Category
      </h2>
      <svg width={width} height={height} ref={svgRef}>
        <g>
          {renderData != null
            ? selectedData.map((datum) => (
                <g key={datum.category}>
                  <rect
                    x={renderData.xScaler(datum.category)}
                    y={Math.min(
                      renderData.yScaler(datum.mean),
                      renderData.yScaler(0)
                    )}
                    height={Math.abs(
                      renderData.yScaler(0) - renderData.yScaler(datum.mean)
                    )}
                    width={renderData.xScaler.bandwidth()}
                    // opacity={0}
                    style={{ opacity: 0 }}
                    fill="steelblue"
                  ></rect>
                  <text
                    x={
                      (renderData.xScaler(datum.category) || 0) +
                      renderData.xScaler.bandwidth() / 2
                    }
                    // the Math.sign ensures that the text is inside for negative bars
                    y={
                      renderData.yScaler(datum.mean) +
                      (Math.sign(datum.mean) === 1
                        ? 12 + LABEL_BAR_PADDING
                        : -1 * LABEL_BAR_PADDING)
                    }
                    textAnchor="middle"
                    fill="white"
                  >
                    {numToDollars(datum.mean)}
                  </text>
                </g>
              ))
            : "Loading..."}
        </g>
      </svg>
    </div>
  );
};

export default CategoryProfitBar;
