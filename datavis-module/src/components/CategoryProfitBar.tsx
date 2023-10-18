import { useEffect, useState, useRef, RefObject } from "react";
import * as d3 from "d3";

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
  }, [data]);
  // TODO: make this useEffect dependent on user input
  useEffect(() => {
    const newSelectedData = Object.entries(categoryData).map(
      ([category, datum]) => ({ category: category, mean: datum.mean })
    );
    setSelectedData(newSelectedData);
  }, [categoryData]);
  const svgRef = useRef<SVGSVGElement | null>(null);

  const categoryList = selectedData.map((datum) => datum.category);
  const x = d3.scaleBand().domain(categoryList).range([0, width]).padding(0);
  console.log(x.bandwidth());
  const means = Object.values(selectedData).map((datum) => datum.mean);
  const y = d3
    .scaleLinear()
    .domain([d3.min(means) || 0, d3.max(means) || 0])
    .range([height, 0]);
  const marginLeft = 32;
  // Using refs here may be hacky, but it's better than working directly w/ SVGs like this recommends:
  //   https://2019.wattenberger.com/blog/react-and-d3
  useEffect(() => {
    const svgElement = d3.select(svgRef.current);
    const axisGenerator = d3.axisBottom(x);
    svgElement.append("g").call(axisGenerator);
    svgElement
      .append("g")
      .attr("transform", `translate(${marginLeft},0)`)
      .call(d3.axisLeft(y))
      .call((g) =>
        g
          .append("text")
          .attr("x", -1 * marginLeft)
          .attr("y", 10)
          .attr("fill", "currentColor")
          .attr("text-anchor", "middle")
          .text("Mean Profit")
      );
  }, [selectedData, svgRef]);
  return (
    <svg width={width} height={height} ref={svgRef}>
      <g>
        {selectedData.map((datum) => (
          <rect
            key={datum.category}
            x={x(datum.category)}
            y={y(datum.mean)}
            height={y(0) - y(datum.mean)}
            width={x.bandwidth()}
            fill="steelblue"
          ></rect>
        ))}
      </g>
    </svg>
  );
};

export default CategoryProfitBar;
