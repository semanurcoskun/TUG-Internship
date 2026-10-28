import TargetCard from "./TargetCard";
function TargetList({ targets, timeMode }) {
    return (
        <div className="target-list">
            {targets.map((target) => (
                <TargetCard key={target.name} target={target} timeMode={timeMode} />
            ))}
        </div>
    );
}

export default TargetList;