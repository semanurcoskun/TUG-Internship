import {getLocalDate, formatTimeForDisplay } from "./utils";
import * as XLSX from 'xlsx';

export const exportToExcel = (data, timeMode, obsDate) => {
    if (!data || !data.ranked_targets) return;

    const formattedData = data.ranked_targets.map(target => ({
        "Target Name": target.name,
        "Overall Score": target.score,

        // saatler
        "Window Start": formatTimeForDisplay(target.window_start_utc, timeMode),
        "Window End": formatTimeForDisplay(target.window_end_utc, timeMode),
        "Best Time": formatTimeForDisplay(target.best_time_utc, timeMode),
        
        // astronomi
        "Alt °": target.best_altitude?.toFixed(2) || "",
        "Airmass": target.best_airmass?.toFixed(2) || "",
        "Moon Separation °": target.moon_separation_deg?.toFixed(2) || "",
        "Moon Illumination": target.moon_illumination?.toFixed(2) || "",

        // weather
        "Cloud Cover %": target.cloud_cover?.toFixed(2) || "",
        "Temperature °C": target.temperature_2m?.toFixed(1) || "",
        "Wind Speed km/h": target.wind_speed_10m?.toFixed(1) || "",
        "Humidity %": target.relative_humidity_2m?.toFixed(1) || "",

        // observability
        "Observable": target.observable ? "Yes" : "No",
        "Observable Minutes": target.observable_minutes || 0,
        "Continuity": target.window_is_continuous ? "Continuous" : "Discontinuous",
        "Rejection Reasons": target.rejection_reasons?.join(", ") || "",

        //score nreakdown
        "Score: Airmass": target.score_breakdown?.airmass?.toFixed(2) || "",
        "Score: Altitude": target.score_breakdown?.altitude?.toFixed(2) || "",
        "Score: Moon Sep": target.score_breakdown?.moon_separation?.toFixed(2) || "",
        "Score: Moon Illum": target.score_breakdown?.moon_illumination?.toFixed(2) || "",
        "Score: Cloud Cover": target.score_breakdown?.cloud_cover?.toFixed(2) || ""
    }));

    const worksheet = XLSX.utils.json_to_sheet(formattedData);
    const wscols = [
    { wch: 15 }, { wch: 12 }, { wch: 20 }, { wch: 20 }, { wch: 20 },
    { wch: 10 }, { wch: 10 }, { wch: 15 }, { wch: 15 }, { wch: 15 },
    { wch: 10 }, { wch: 12 }, { wch: 12 }, { wch: 15 }, { wch: 15 },
    { wch: 15 }, { wch: 17 }, { wch: 15 }
    ];
    worksheet['!cols'] = wscols;

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Observation Plan");
    const finalDate = obsDate || getLocalDate(); // Use provided obsDate or fallback to local date
    XLSX.writeFile(workbook, `Observation_Plan_${finalDate}.xlsx`);
};
