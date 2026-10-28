import ScoreBreakdown from "./ScoreBreakdown";
import TargetMetrics from "./TargetMetrics";

import {formatTimeForDisplay} from "./utils";

function TargetCard({ target, timeMode }) {
    if (!target.observable) {
        return (
            <div className = "target-card unobservable">
                <h3> {target.name } </h3>
                <p>This target is not observable tonight.</p>
                <TargetMetrics target={target} />
                <ul className="rejection-reasons">
                    {target.rejection_reasons.map((reason, i) => (
                        <li key={i}>{reason}</li>
                    ))}
                </ul>
            </div>
        );
    }

    const continuityLabel = target.window_is_continuous ? "Continuous" : "Discontinuous";

    return (
    <div className="target-card">
      <h3>{target.name} <span className="score-badge">{target.score.toFixed(2)}</span></h3>
      <p>
        {formatTimeForDisplay(target.window_start_utc, timeMode)} - {formatTimeForDisplay(target.window_end_utc, timeMode)}
      </p>
      <p className="window-meta">
        {target.observable_minutes} minutes observable. <br />
        {continuityLabel} window.
      </p>
      <p>Best time: {formatTimeForDisplay(target.best_time_utc, timeMode)}</p>
      <TargetMetrics target={target} />
      {/* <pre>{JSON.stringify(target.score_breakdown, null, 2)}</pre> */}
      <ScoreBreakdown breakdown={target.score_breakdown} />
    </div>        
    );
}

export default TargetCard;