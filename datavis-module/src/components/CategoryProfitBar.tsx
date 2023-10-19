import { useEffect, useState, useRef, useCallback, RefObject } from "react";
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

type CategoryLists = {
  [category: string]: number[];
};

type SubcategoryLists = {
  [category: string]: {
    [subcategory: string]: number[];
  };
};

type BarDatum = {
  category: string;
  mean: number;
};

const CategoryProfitBar = (props: ICategoryProfitBarProps) => {
  const { data, height, width } = props;
  const [categoryData, setCategoryData] = useState<TCategoryData>({});
  const [subcategoryData, setSubcategoryData] = useState<TSubcategoryData>({});
  const [selectedData, setSelectedData] = useState<BarDatum[]>([]);
  const [currentCategory, setCategory] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  useEffect(() => {
    const categoryProfitLists: CategoryLists = {};
    const subcategoryProfitLists: SubcategoryLists = {};
    // First, we go through the data, row by row,
    //   and add each datum's profit to a list corresponding to that datum's category and subcategory
    for (const row of data) {
      const category = row["Category"];
      // For our purposes, we just discard rows with no given category
      if (category == "") continue;
      const subcategory = row["Sub-Category"];
      if (!(category in categoryProfitLists)) {
        categoryProfitLists[category] = [];
        subcategoryProfitLists[category] = { [subcategory]: [] };
      }
      const profit = Number(row["Profit"]);
      categoryProfitLists[category].push(profit);

      // Skip the subcategory processing if it's blank
      if (subcategory == "") continue;
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
  // Updates the selectedData to either the subcategories of category, or the categories if the input is null
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
          .attr("x", marginLeft)
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
    [subcategoryData, categoryData, setSelectedData, svgRef]
  );

  useEffect(() => {
    console.log("run");
    const svgElement = d3.select(svgRef.current);
    const bars = svgElement
      .selectAll("rect")
      .transition()
      .duration(100)
      .ease(d3.easeLinear)
      .style("opacity", 1);
    // .attr("opacity", 0);
  }, [selectedData, svgRef]);

  const marginLeft = 108;
  const marginBottom = 32;
  const marginTop = 32;
  const categoryList = selectedData.map((datum) => datum.category);
  const x = d3
    .scaleBand()
    .domain(categoryList)
    .range([marginLeft, width])
    .padding(0.1);
  const means = Object.values(selectedData).map((datum) => datum.mean);
  const maxMean = d3.max(means) || 0;
  const graphMax = maxMean * 1.5;
  const minMean = d3.min(means) || 0;
  const graphMin = minMean >= 0 ? 0 : minMean * 1.5;
  console.log(graphMin, graphMax);
  const y = d3
    .scaleLinear()
    .domain([graphMin, graphMax])
    .range([height - marginBottom, marginTop]);

  // Using refs here may be hacky, but it's better than working directly w/ SVGs like this recommends:
  //   https://2019.wattenberger.com/blog/react-and-d3
  useEffect(() => {
    const svgElement = d3.select(svgRef.current);
    // Clears previously rendered axes
    svgElement.selectAll(".axis").remove();
    svgElement
      .append("g")
      .call(d3.axisBottom(x))
      .attr("transform", `translate(0,${height - marginBottom})`)
      .attr("class", "axis x-axis");
    svgElement
      .append("g")
      .call(d3.axisLeft(y))
      .call((g) =>
        g
          .append("text")
          .attr("x", -1 * marginLeft + 4)
          .attr("y", y((graphMax - graphMin) / 2))
          .attr("fill", "currentColor")
          .attr("text-anchor", "start")
          .attr("font-size", 12)
          .text("Mean Profit ($)")
      )
      .attr("transform", `translate(${marginLeft},0)`)
      .attr("class", "axis");
    if (minMean < 0) {
      svgElement
        .append("line")
        .style("stroke", "black")
        .style("stroke-width", 1)
        .attr("class", "zero-line")
        .attr("x1", marginLeft)
        .attr("y1", y(0))
        .attr("x2", width)
        .attr("y2", y(0));
    } else {
      svgElement.selectAll(".zero-line").remove();
    }
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
  }, [selectedData, svgRef]);
  return (
    <svg width={width} height={height} ref={svgRef}>
      <g>
        {selectedData.map((datum) => (
          <rect
            key={datum.category}
            x={x(datum.category)}
            y={Math.min(y(datum.mean), y(0))}
            height={Math.abs(y(0) - y(datum.mean))}
            width={x.bandwidth()}
            // opacity={0}
            style={{ opacity: 0 }}
            fill="steelblue"
          ></rect>
        ))}
      </g>
    </svg>
  );
};

export default CategoryProfitBar;
