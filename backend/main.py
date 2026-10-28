from fastapi import FastAPI, APIRouter
from scoring import evaluate_target, WEATHER_WARNING, WEATHER_FORECAST_DAYS
from weather_service import get_hourly_weather, match_weather_to_time_sequence
from calculations import get_time_sequence, compute_target_metrics
from astronomy_service import get_target_coordinates, load_targets, parse_targets_file
from calculations import get_time_sequence
from astropy.coordinates import EarthLocation
from astropy import units as u
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
import ollama
from ai_service import ask_ollama, ask_ollama_stream, build_prompt
from typing import List, Dict, Any
from observatories import get_observatories
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    location: Dict[str, Any]
    night: Dict[str, Any]
    ranked_targets: List[Dict[str, Any]]
    history: List[Message] = []


def is_weather_available(time_sequence):
    obs_Date = time_sequence[0].datetime.date()
    days_ahead = (obs_Date - datetime.now(timezone.utc).date()).days
    return days_ahead <= WEATHER_FORECAST_DAYS

class AskRequest(BaseModel):
    question: str
    location: dict
    night: dict
    ranked_targets: List[Dict[str, Any]]
    history: List[Dict[str, Any]] = []


app = FastAPI(title = "Astronomy and Weather API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True,
)

@app.get("/api/weather")
async def fetch_weather(observatory: str, obs_date: str):
    try:
        location = EarthLocation.of_site(observatory)
    except Exception as e:
        return {"error": f"Error fetching observatory location: {str(e)}"}

    time_sequence = get_time_sequence(obs_date, location)
    start_date = time_sequence[0].datetime.strftime("%Y-%m-%d")
    end_date = time_sequence[-1].datetime.strftime("%Y-%m-%d")   

    weather_data = await get_hourly_weather(location, start_date, end_date)
    if isinstance(weather_data, dict) and "error" in weather_data:
        return weather_data

    return {
        "Coordinates": {"lat": location.lat.deg, "lon": location.lon.deg},
        "night": {"sunset_to_sunrise": [time_sequence[0].iso, time_sequence[-1].iso]},
        "weather": weather_data.to_dict(orient="records")
    }


@app.get("/api/targets")
def get_all_targets():
    return load_targets()

@app.get("/api/targets/{target_id}")
def get_single_target(target_id: str):
    return get_target_coordinates(target_id)

@app.get("/api/rank")
async def rank_targets(observatory: str, obs_date: str, obs_time: str):
    try:
        location = EarthLocation.of_site(observatory) 
    except Exception as e:
        return {"error": f"Error fetching observatory location: {str(e)}"}

    full_date = f"{obs_date} {obs_time}"
    time_sequence = get_time_sequence(full_date, location)
    start_date = time_sequence[0].datetime.strftime("%Y-%m-%d")
    end_date = time_sequence[-1].datetime.strftime("%Y-%m-%d")

    weather_available = is_weather_available(time_sequence)
    if weather_available:
        weather_df = await get_hourly_weather(location, start_date, end_date)
        if isinstance(weather_df, dict) and "error" in weather_df:
            return {"error": f"Error fetching weather data: {weather_df['error']}"}
        weather = match_weather_to_time_sequence(weather_df, time_sequence)
    else:
        weather = None


    targets = load_targets()
    if isinstance(targets, dict) and "error" in targets:
        return targets

    results = []
    for target in targets:
        metrics = compute_target_metrics(target, location, time_sequence)
        result = evaluate_target(target, metrics, weather, time_sequence, weather_available=weather_available)
        results.append(result)

    # observable = [r for r in results if r["observable"]]
    # observable.sort(key=lambda r: r["score"], reverse=True)
    results.sort(key=lambda r: (not r["observable"], -r.get("score", 0)))
    observable_count = sum(1 for r in results if r["observable"])

    response = {
        "location": {
            "site": observatory.upper(), 
            "lat": location.lat.deg, 
            "lon": location.lon.deg, 
            "height": location.height.value
        },
        "night": {"sunset": time_sequence[0].iso, "sunrise": time_sequence[-1].iso},
        "total_targets": len(results),
        "observable_count": observable_count,
        "ranked_targets": results,
        "weather_reliable": weather_available,
    }

    if not weather_available:
        response["warning"] = WEATHER_WARNING

    return response


@app.post("/api/rank-upload")
async def rank_targets_upload(
    observatory: str = Form(...),
    obs_date: str = Form(...),
    obs_time: str = Form(...),
    targets_file: UploadFile = File(...),
):
    try:
        location = EarthLocation.of_site(observatory)
    except Exception as e:
        return {"error": f"Error fetching observatory location: {str(e)}"}

    content = await targets_file.read()
    targets = parse_targets_file(targets_file.filename, content)
    if isinstance(targets, dict) and "error" in targets:
        return targets

    time_sequence = get_time_sequence(obs_date, location)
    start_date = time_sequence[0].datetime.strftime("%Y-%m-%d")
    end_date = time_sequence[-1].datetime.strftime("%Y-%m-%d")

    weather_available = is_weather_available(time_sequence)
    if weather_available:
        weather_df = await get_hourly_weather(location, start_date, end_date)
        if isinstance(weather_df, dict) and "error" in weather_df:
            return {"error": f"Error fetching weather data: {weather_df['error']}"}
        weather = match_weather_to_time_sequence(weather_df, time_sequence)
    else:
        weather = None

        
    results = []
    for target in targets:
        metrics = compute_target_metrics(target, location, time_sequence)
        result = evaluate_target(target, metrics, weather, time_sequence)
        results.append(result)

    # observable = [r for r in results if r["observable"]]
    # observable.sort(key=lambda r:r["score"], reverse=True)
    results.sort(key=lambda r: (not r["observable"], -r.get("score", 0)))
    observable_count = sum(1 for r in results if r["observable"])

    response = {
        "location": {
            "site": observatory.upper(),
            "lat": location.lat.deg,
            "lon": location.lon.deg,
            "height": location.height.value,
        },
        "night": {"sunset": time_sequence[0].iso, "sunrise": time_sequence[-1].iso},
        "total_targets": len(results),
        "observable_count": observable_count,
        "ranked_targets": results,
        "weather_reliable": weather_available
    }   

    if not weather_available:
        response["warning"] = WEATHER_WARNING

    return response

@app.post("/api/ask")
async def ask(payload:AskRequest):
    prompt = build_prompt(payload.location, payload.night, payload.ranked_targets)
    messages = [{"role": "system", "content": prompt}]
    messages.extend(payload.history)
    messages.append({"role": "user", "content": payload.question})
    try:
        answer = await ask_ollama(messages)
    except Exception as e:
        return {"error": f"Error occurred while asking Ollama: {str(e)}"}

    return {"answer": answer}


@app.get("/api/observatories")
def fetch_observatories():
    return get_observatories(force_refresh=False)

@app.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    prompt = build_prompt(request.location, request.night, request.ranked_targets)
    messages = [{"role": "system", "content": prompt}]
    for m in request.history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": request.question})
    async def event_generator():
        async for piece in ask_ollama_stream(messages):
            yield f"data: {piece}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")