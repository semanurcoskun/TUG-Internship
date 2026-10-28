function LoadingOverlay({text = "Loading..."}) {
    return(
        <div className="loading-overlay">
            <div className="loading-spinner" />
            <span className="loading-text">{text}</span>
        </div>
    );
}

export default LoadingOverlay;