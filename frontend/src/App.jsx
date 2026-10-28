import { useState, useEffect } from "react";
import TargetList from "./components/TargetList";
import ObservationForm from "./components/ObservationForm";
import FilterTabs from "./components/FilterTabs";
import Pagination from "./components/Pagination";
import AskBox from "./components/AskBox";
import {formatTimeForDisplay} from "./components/utils";
import {exportToExcel} from "./components/excel";

const PAGE_SIZE = 9;

function App() {
  const [data, setData] = useState(null);
  const [resultKey, setResultKey] = useState(0);
  const [filter, setFilter] = useState("observable");
  const [page, setPage] = useState(1);
  const [currentTimeMode, setCurrentTimeMode] = useState("Local");
  const [currentObsDate, setCurrentObsDate] = useState(""); // New state for observation date


  // const [error, setError] = useState(null);

  // useEffect(() => {
  //   fetch("http://localhost:8000/api/rank?observatory=TUG&obs_date=2026-08-08 18:00:00")
  //     .then((res) => res.json())
  //     .then((json) => setData(json))
  //     .catch((err) => setError(err.message));
  // }, []);
  // bu method halihazırda olan atrgets.json dosyası içindi ama artık user input istiyoruz

  //if (error) return <p>Error: {error}</p>;
  // if (!data) return <p>Loading...</p>;

  const handleResults = (result, mode, obs_date) => {
    setData(result);
    setFilter("observable");
    setPage(1);
    setResultKey((prev) => prev + 1);
    setCurrentTimeMode(mode); //in each new query, chatbot resets
    setCurrentObsDate(obs_date); // Update the observation date when new results are received
  }
  
  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setPage(1);
    // filtre değişince sayfa1e döner
  };

  let filteredTargets = []
  if (data) {
    filteredTargets = data.ranked_targets.filter((target) => {
      if (filter === "observable") return target.observable;
      if (filter === "unobservable") return !target.observable;
      return true;
    });
  }

  const totalPages = Math.ceil(filteredTargets.length / PAGE_SIZE);
  const pageTargets  = filteredTargets.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div>
      <h1>Observation Planning Assistant</h1>
      <ObservationForm onResults={handleResults} />
      {/* {error && <p style={{ color: "red" }}>{error}</p>} */}
      {data && (
        <>
          <p className="night-info">{data.location.site} — {formatTimeForDisplay(data.night.sunset, currentTimeMode)} / {formatTimeForDisplay(data.night.sunrise, currentTimeMode)} {currentTimeMode === "UTC" ? "UTC" : "Local"}</p>
          
          <div className="summary-container">
            <p className="summary-line">
              {data.observable_count} / {data.total_targets} targets can be observed.
            </p>
            
            <button 
              className="export-excel-btn" 
              onClick={() => exportToExcel(data, currentTimeMode, currentObsDate)} // Pass the current observation date to the export function
            >
              Download as Excel (.xlsx)
            </button>
          </div>

          {data.weather_reliable === false && (
            <div className="weather-warning-banner" role="alert">
              <span className="weather-warning-icon"></span>
              <span>{data.warning}</span>
            </div>
          )}

          <AskBox key={resultKey} location={data.location} night={data.night} rankedTargets={data.ranked_targets} />
          <FilterTabs filter={filter} onChange={handleFilterChange} />

          {filteredTargets.length === 0 ? (
            <p className="empty-state">No targets match the selected filter.</p>
          ) : (
            <>
              <TargetList targets={pageTargets} timeMode={currentTimeMode} />
              <Pagination page={page} totalPages={totalPages} onChange={setPage} />
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;