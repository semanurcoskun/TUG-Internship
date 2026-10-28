function FilterTabs({filter, onChange}) {
    const tabs = [
        {key: "observable", label: "Observable"},
        {key: "unobservable", label: "Unobservable"},
        {key: "all", label: "All"}
    ];

    return (
        <div className="filter-tabs">
            {tabs.map((tab) => (
                <button
                    key={tab.key}
                    className={filter ===tab.key ? "filter-tab active" : "filter-tab"}
                    onClick={() => onChange(tab.key)}
                >
                    {tab.label}
                </button>
            ))}
        </div>
    );
}

export default FilterTabs;