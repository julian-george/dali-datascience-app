import * as d3 from "d3";
import { useState, useEffect, useCallback } from "react";
import { feature } from "topojson-client";
import { Topology, GeometryCollection } from "topojson-specification";
import "../App.css";
import us from "../counties-albers-10m.json";
import zipfips from "../zipfips.json";

interface ILocationQuantityMapProps {
  data: any[];
  height: number;
  width: number;
}

type TLocationData = {
  [state: string]: number;
};

type TCircleData = {
  id: number;
  numOrders: number;
  title: string;
  centroid: any;
  radius: number;
};

const usTopo = us as unknown as Topology;
const zipToFips = zipfips as unknown as {
  [zip: string]: { STCOUNTYFP: number };
};

const MIN_BUBBLE_SIZE = 2;
const MAX_BUBBLE_SIZE = 25;

const LocationQuantityMap = ({
  data,
  width,
  height,
}: ILocationQuantityMapProps) => {
  // SVG path to draw the USA outline
  const [countryPath, setCountryPath] = useState<string | undefined>();
  // SVG paths to draw state outlines
  const [statePaths, setStatePaths] = useState<(string | undefined)[]>([]);
  // Data to map over to render state & county bubbles
  const [stateCircleData, setStateCircleData] = useState<TCircleData[]>();
  const [countyCircleData, setCountyCircleData] = useState<TCircleData[]>();
  // Geopath function that converts points/paths to svg positions
  const [pathProjection, setPathProjection] = useState<d3.GeoPath>();
  // Number of purchases by states and counties
  const [stateData, setStateData] = useState<TLocationData | null>(null);
  const [countyData, setCountyData] = useState<TLocationData | null>(null);
  // Whether the user is viewing data for states or counties
  const [vizMode, setVizMode] = useState<"STATE" | "COUNTY">("COUNTY");

  // Building the dict with state/county purchases
  useEffect(() => {
    const newStateData: TLocationData = {};
    const newCountyData: TLocationData = {};
    for (const row of data) {
      const state = row["State"];
      if (state !== "") {
        if (!(state in newStateData)) {
          newStateData[state] = 1;
        } else {
          newStateData[state]++;
        }
      }

      const zipCode = parseInt(row["Postal Code"]).toString();
      if (zipCode !== "") {
        // We use each county's unique "FIPS" code as the object index
        const fipsCode = zipToFips?.[zipCode]?.["STCOUNTYFP"] || null;
        if (fipsCode) {
          if (!(fipsCode in newCountyData)) {
            newCountyData[fipsCode] = 1;
          } else {
            newCountyData[fipsCode]++;
          }
        }
      }
    }
    setStateData(newStateData);
    setCountyData(newCountyData);
  }, [data, setStateData, setCountyData]);

  // Iterate through all states and counties and add them, w/ svg positioning/size, to the circle datas
  useEffect(() => {
    if (!stateData || !countyData || !pathProjection) return;

    const stateRadius = d3.scaleSqrt(
      [0, Math.max(...Object.values(stateData))],
      [MIN_BUBBLE_SIZE, MAX_BUBBLE_SIZE]
    );
    const newStateCircleData = feature(
      usTopo,
      usTopo.objects.states as GeometryCollection
    ).features.map((currFeature) => {
      const stateName = (currFeature.properties as { name: string })["name"];
      const numOrders = stateData[stateName];
      return {
        id: currFeature.id as number,
        title: stateName,
        centroid: pathProjection.centroid(currFeature),
        numOrders,
        radius: stateRadius(numOrders),
      };
    });
    setStateCircleData(newStateCircleData);
    const countyRadius = d3.scaleSqrt(
      [0, Math.max(...Object.values(countyData))],
      [MIN_BUBBLE_SIZE, MAX_BUBBLE_SIZE]
    );

    const newCountyCircleData = feature(
      usTopo,
      usTopo.objects.counties as GeometryCollection
    ).features.map((currFeature) => {
      const fipsId = currFeature.id as number;
      const countyName = (currFeature.properties as { name: string })["name"];
      const numOrders = countyData?.[fipsId] || 0;
      return {
        id: currFeature.id as number,
        title: countyName,
        centroid: pathProjection.centroid(currFeature),
        numOrders,
        radius: countyRadius(numOrders),
      };
    });
    setCountyCircleData(newCountyCircleData);
  }, [stateData, countyData, pathProjection]);

  // Create projection function and add to state
  useEffect(() => {
    const newGeoPath = d3.geoPath();
    setPathProjection(() => newGeoPath);
  }, [setPathProjection]);

  // Fade in and out the circle labels upon mouse entering and exiting the circle
  const bubbleOnMouseEnter = useCallback(
    (e: React.MouseEvent<SVGCircleElement, MouseEvent>) => {
      // @ts-ignore
      d3.select(e.target.parentNode)
        .select("text")
        .transition()
        .duration(50)
        .ease(d3.easeLinear)
        .style("opacity", 1);
    },
    []
  );

  const bubbleOnMouseLeave = useCallback(
    (e: React.MouseEvent<SVGCircleElement, MouseEvent>) => {
      // @ts-ignore
      d3.select(e.target.parentNode)
        .select("text")
        .transition()
        .duration(50)
        .ease(d3.easeLinear)
        .style("opacity", 0);
    },
    []
  );

  // Add the projected country and state paths to state
  useEffect(() => {
    if (!pathProjection) return;
    setCountryPath(
      pathProjection(
        feature(usTopo, usTopo.objects.nation as GeometryCollection).features[0]
      ) || undefined
    );
    setStatePaths(
      feature(usTopo, usTopo.objects.states as GeometryCollection).features.map(
        (feature, i) => pathProjection(feature) || undefined
      )
    );
  }, [setCountryPath, setStatePaths, pathProjection]);

  return (
    <div className="map-container">
      <h2 style={{ textAlign: "center" }}>
        Number of Purchases By County and State
      </h2>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <g>
          <path d={countryPath} fill="white" stroke="black"></path>
          {statePaths.map((statePath, i) => (
            <path key={i} d={statePath} fill="white" stroke="grey"></path>
          ))}
        </g>
        <g>
          {(vizMode === "STATE" ? stateCircleData : countyCircleData)?.map(
            (circleData) =>
              circleData.numOrders > 0 ? (
                <g
                  key={circleData.id}
                  className="bubble"
                  onMouseEnter={bubbleOnMouseEnter}
                  onMouseLeave={bubbleOnMouseLeave}
                >
                  <circle
                    transform={`translate(${circleData.centroid})`}
                    r={circleData.radius}
                    fill="steelblue"
                    opacity="0.8"
                  ></circle>
                  <text
                    transform={`translate(${circleData.centroid})`}
                    fill="#444"
                    textAnchor="middle"
                    fontSize="12.5"
                    dy={-1 * circleData.radius - 2}
                    opacity="0"
                    pointerEvents="none"
                    fontWeight={500}
                  >
                    {circleData.title} - {circleData.numOrders}
                  </text>
                </g>
              ) : (
                <g key={circleData.id} />
              )
          )}
        </g>
      </svg>
      <div className="map-button-row">
        <button
          disabled={vizMode === "STATE"}
          onClick={() => {
            setVizMode("STATE");
          }}
        >
          State Data
        </button>
        <button
          disabled={vizMode === "COUNTY"}
          onClick={() => {
            setVizMode("COUNTY");
          }}
        >
          County Data
        </button>
      </div>
    </div>
  );
};
export default LocationQuantityMap;
