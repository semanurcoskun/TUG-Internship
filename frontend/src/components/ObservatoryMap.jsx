import { useEffect, useState }from "react";
import { MapContainer, TileLayer, Marker, Popup, useMapEvents }from "react-leaflet";
import "leaflet/dist/leaflet.css";

function ObservatoryMap({ onSelect }) {
    const [observatories, setObservatories] = useState([]);

    useEffect(() => {
        fetch("http://localhost:8000/api/observatories")
        .then((res) => res.json())
        .then(setObservatories)
        .catch((err) => setObservatories([]));
    }, []); 

    return (
        <div className="observatory-map">
            <MapContainer center={[20, 20]} zoom={2} style={{height:"350px", width:"100%"}}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap contributors'
                />
                {observatories.map((obs) => (
                    <Marker
                        key={obs.name}
                        position= {[obs.lat, obs.lon]}
                        eventHandlers={{click: () => onSelect(obs.name)}}
                    >
                    <Popup>{obs.name}</Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>    
    );
}

export default ObservatoryMap;