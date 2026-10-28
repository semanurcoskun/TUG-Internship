function ScoreBreakdown({breakdown}) {
    const labels = {
        airmass: "Airmass",
        altitude: "Altitude",
        moon_separation: "Moon Separation",
        moon_illumination: "Moon Illumination",
        cloud_cover: "Cloud Cover",
    };


    return (
        <div className = "score-breakdown">
            {Object.entries(breakdown).map(([key, value]) => (
                <div key={key} className="score-bar-row">
                    <span className="score-bar-label">{labels[key] || key}</span>
                    <div className="score-bar-track">
                    <div
                        className="score-bar-fill"
                        style={{ width: `${(value / 0.3) * 100}%` }}
                    />
                </div>
                <span className="score-bar-value">{value.toFixed(2)}</span>
                {/* return string, how many digits after decimal point */}
            </div>
            ))}
        </div>
    );
}

export default ScoreBreakdown;