import {useState} from "react";
import ObservatoryMap from "./ObservatoryMap";
import LoadingOverlay from "./LoadingOverlay";
import {getLocalDate, getLocalTime, getUTCTime, getUTCDate} from "./utils";


 function ObservationForm({onResults}) {
    const [observatory, setObservatory]= useState("TUG");
    const [file, setFile] = useState(null);
    const [loading, setLoading]= useState(false);
    const [error, setError] = useState(null);

    const [inputType, setInputType] = useState("file");
    const [rawText, setRawText] = useState("");

    const [timeMode, setTimeMode] = useState("Local");
    const [obsTime, setObsTime] = useState(getLocalTime());
    const [obsDate, setObsDate] = useState(getLocalDate());
    

    const handleTimeModeChange = (mode) => {
      setTimeMode(mode);
      if (mode === "UTC") {
        setObsDate(getUTCDate());
        setObsTime(getUTCTime());   
      } else {
        setObsDate(getLocalDate());
        setObsTime(getLocalTime());
      }
    }

    const handleSubmit = async(e) => {
      e.preventDefault();
      setError(null);
      setLoading(true);

    // bu satırlar boş dosya kabul edilmediğinde kullanılıyordu anma şu an boş dosya yerine bizim targets.json dosyamız kullanılıyoor
    //   if (!file) {
    //     setError("Please upload a target list file.");
    //     return;
    //   }
    
    //   const formData = new FormData();
    //   formData.append("observatory", observatory);
    //   formData.append("obs_date", obs_date);
    //   formData.append("obs_time", obs_time);
    //   formData.append("targets_file", file);

    //   setLoading(true);
    //   try {
    //     const res = await fetch("http://localhost:8000/api/rank-upload", {
    //       method: "POST",
    //       body: formData,
    //     });
    //     const data = await res.json();

    //     if (data.error) {
    //       setError(data.error);
    //     } else{
    //       onResults(Data);
    //     }
    //   } catch (Err) {
    //     setError(Err.message);
    //   } finally {
    //     setLoading(false);
    //   }
    // };


    try {
      let finalDate = obsDate;
      let finalTime = obsTime; 
      if (timeMode === "Local") {
        const localDateTime = new Date(`${obsDate}T${obsTime}`);
        finalDate = `${localDateTime.getUTCFullYear()}-${String(localDateTime.getUTCMonth() + 1).padStart(2, '0')}-${String(localDateTime.getUTCDate()).padStart(2, '0')}`;
        finalTime = `${String(localDateTime.getUTCHours()).padStart(2, '0')}:${String(localDateTime.getUTCMinutes()).padStart(2, '0')}:${String(localDateTime.getUTCSeconds()).padStart(2, '0')}`;
      }
      let res;

      if (file || (inputType === "text" && rawText.trim() !== "")) {
        const formData = new FormData();
        formData.append("observatory", observatory);
        formData.append("obs_date", finalDate);
        formData.append("obs_time", finalTime);

        // Eğer kullanıcı text seçtiyse metinden sahte bir dosya yaratıyoruz
        let uploadFile = file;
        if (inputType === "text" && rawText) {
          // Metnin JSON mu yoksa CSV mi olduğunu köşeli parantezden anlıyoruz
          const isJson = rawText.trim().startsWith("[");
          const filename = isJson ? "pasted_targets.json" : "pasted_targets.csv";
          const blob = new Blob([rawText], { type: "text/plain" });
          uploadFile = new File([blob], filename);
        }

        formData.append("targets_file", uploadFile);

        res = await fetch("http://localhost:8000/api/rank-upload", {
          method: "POST",
          body: formData,
        });
      } else { //dosya yüklenmediyse targets.json dosyasını kullan
          const params = new URLSearchParams({observatory, obs_date: finalDate, obs_time: finalTime})
          res = await fetch('http://localhost:8000/api/rank?' + params);
      }

      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        onResults(data, timeMode, obsDate); 
      }
    } catch(err)  {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {loading && <LoadingOverlay text="Loading... Please wait."/>}
      <div>
        <label>Observatory:</label>
        <input
          id="observatory-input"
          name="observatory"
          type="text"
          value={observatory}
          onChange={(e) => setObservatory(e.target.value)}
          placeholder = "exp: TUG"
        />
        <ObservatoryMap onSelect={(name) => setObservatory(name)} />
      </div>

      {/* <div>
        <label>Target File (JSON/CSV): </label>
        <input
        type="file"
          accept = ".json, .csv"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <p style={{ fontSize: "0.85em", color: "#666" }}>
          If no file is uploaded, the default Messier Catalog will be used.<br />
          You can upload a JSON or CSV file with your own target list.<br />
          The file should contain an array of objects, each with a "name" and "coordinates" field.<br />
          JSON: [{"{"}"id": "M1", "name": "...", "ra": "...", "dec": "...", "type": "..."{"}"}]<br />
          CSV: id,name,ra,dec,type<br />
        </p>  
      </div> */}

      <div className="target-input-section">
        <label>Target Input Method:</label>
        
        <div className="toggle-group">
          <label className="radio-label">
            <input
              id="inputType-file"
              name="inputType"
              type="radio" 
              value="file" 
              checked={inputType === "file"} 
              onChange={() => setInputType("file")} 
            />
            Upload File
          </label>
          <label className="radio-label">
            <input
              id="inputType-text"
              name="inputType"
              type="radio" 
              value="text" 
              checked={inputType === "text"} 
              onChange={() => setInputType("text")} 
            />
            Paste Text
          </label>
        </div>

        {inputType === "file" ? (
          <input
            id="file-upload-input"
            name="fileUpload"
            type="file"
            accept=".json, .csv"
            onChange={(e) => setFile(e.target.files[0])}
            className="file-input"
          />
        ) : (
          <textarea
            id="text-upload-input"
            name="textUpload"
            rows="6"
            className="text-input-area"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder='Paste your JSON array or CSV text here...&#10;JSON: [{"id": "M1", "ra": "...", ...}]&#10;CSV: id,name,ra,dec'
          />
        )}
        
        <p className="help-text">
          If no file/text is provided, the default Messier Catalog will be used.<br />
          You can provide your own target list via file upload or text paste.<br />
          JSON: [{"{"}"id": "M1", "name": "...", "ra": "...", "dec": "...", "type": "..."{"}"}]<br />
          CSV: id,name,ra,dec,type<br />
        </p>  
      </div>

      {/* ZAMAN DİLİMİ TOGGLE */}
      <div style={{ marginBottom: "15px" }}>
        <label>Timezone:</label>
        <div className="toggle-group">
          <label className="radio-label">
            <input
              id="timeMode-local"
              name="timeMode"
              type="radio" 
              value="Local" 
              checked={timeMode === "Local"} 
              onChange={() => handleTimeModeChange("Local")} 
            />
            Local Time
          </label>
          <label className="radio-label">
            <input
              id="timeMode-utc"
              name="timeMode"
              type="radio" 
              value="UTC" 
              checked={timeMode === "UTC"} 
              onChange={() => handleTimeModeChange("UTC")} 
            />
            UTC
          </label>
        </div>
      </div>

      <div>
        <label>Observation Date (YYYY-MM-DD):</label>
        <input
          id="obs-date-input"
          name="obsDate"
          type ="text"
          value={obsDate}
          onChange = {(e) => setObsDate(e.target.value)}
          placeholder = "YYYY-MM-DD"
        />
      </div>

      <div>
        <label>Observation Time (HH:MM:SS):</label>
        <input
          id="obs-time-input"
          name="obsTime"
          type="text"
          value={obsTime}
          onChange={(e) => setObsTime(e.target.value)}
          placeholder = "HH:MM:SS"
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? "Loading..." : "Submit"}
      </button>

      {error && <p style={{color: "red"}}>{error}</p>}
    </form>
  );
}

export default ObservationForm;