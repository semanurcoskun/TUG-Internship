function TargetMetrics({target}) {
    const weatherReliable = target.weather_reliable !== false;
    return (
        <>
            <div className="metrics-group">
            <span className="metrics-label">Astronomy</span>
            <div className="metrics">
                <span>Alt: {target.best_altitude}°</span>
                <span>Airmass: {target.best_airmass}</span>
                <span>
                Moon: {target.moon_separation_deg}° / %{(target.moon_illumination * 100).toFixed(0)}
                {target.moon_phase && ` (${target.moon_phase})`}
                </span>
            </div>
            </div>

            {weatherReliable ? (
                <div className="metrics-group">
                <span className="metrics-label">Weather</span>
                <div className="metrics">
                    <span>Clouds: %{target.cloud_cover}</span>
                    <span>Temperature: {target.temperature_2m}°C</span>
                    <span>Wind: {target.wind_speed_10m} km/h</span>
                    <span>Humidity: %{target.relative_humidity_2m}</span>
                </div>
                </div>
            ): (
                <div className="metrics-group metrics-group--unavailable">
                <span className="metrics-label">Weather</span>
                <div className="metrics">
                    <span className="metrics-unavailable">No reliable forecast.</span>
                </div>
                </div>
            )}

            {/* <div className="metrics-group">
            <span className="metrics-label">Weather</span>
            <div className="metrics">
                <span>Clouds: %{target.cloud_cover}</span>
                <span>Temperature: {target.temperature_2m}°C</span>
                <span>Wind: {target.wind_speed_10m} km/h</span>
                <span>Humidity: %{target.relative_humidity_2m}</span>
            </div>
            </div>         */}
        </>
    );
}

export default TargetMetrics;