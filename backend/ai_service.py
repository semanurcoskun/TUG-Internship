import ollama
import httpx
import asyncio
import re
import json

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1:8b"
ollama_semaphore = asyncio.Semaphore(1) #limits olllama requests

async def ask_ollama(messages: list):
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        # "options": { this change blew up my pc 
        #     "num-ctx" : 8192
        # }
    }
    async with ollama_semaphore:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", OLLAMA_API_URL, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    content_piece = chunk.get("message", {}).get("content", "")
                    if content_piece:
                        yield content_piece
                    if chunk.get("done"):
                        break


            # response = await client.post(OLLAMA_API_URL, json=payload)
            # response.raise_for_status()
            # data = response.json()

            # raw_content = data["message"]["content"]
            # cleaned_content = re.sub(r'<scratchpad>.*?</scratchpad>', '', raw_content, flags=re.DOTALL).strip()

            # return cleaned_content

async def ask_ollama_stream(messages: list):
    buffer = ""
    in_scratchpad = False
    async for piece in ask_ollama(messages):
        buffer += piece
        # while True:
        #     if not in_scratchpad:
        #         start = buffer.find("<scratchpad>")
        #         if start == -1:
        #             if len(buffer) > 0:
        #                 yield buffer
        #                 buffer = ""
        #             break
        #         else:

        #             if start > 0:
        #                 yield buffer[:start]
        #             buffer = buffer[start + len("<scratchpad>"):]
        #             in_scratchpad = True
        #     else:
        #         end = buffer.find("</scratchpad>")
        #         if end == -1:
        #             buffer = ""
        #             break
        #         else:
        #             buffer = buffer[end + len("</scratchpad>"):]
        #             in_scratchpad = False

        if in_scratchpad:
            # Scratchpad içindeysek kapanışı arıyoruz
            end_idx = buffer.find("</scratchpad>")
            if end_idx != -1:
                # Kapanışı bulduk, sonrasını tut ve scratchpad'den çık
                buffer = buffer[end_idx + len("</scratchpad>"):]
                in_scratchpad = False
            else:
                # Kapanış gelene kadar buffer çok şişmesin diye sadece son 20 karakteri tut
                if len(buffer) > 20: 
                    buffer = buffer[-20:]
            continue
            
        # Scratchpad içinde değilsek açılışı arıyoruz
        start_idx = buffer.find("<scratchpad>")
        if start_idx != -1:
            # Açılışı bulduk! Açılışa kadar olan kısmı gönder (yield et)
            if start_idx > 0:
                yield buffer[:start_idx]
            buffer = buffer[start_idx + len("<scratchpad>"):]
            in_scratchpad = True
        else:
            # Açılış tam yok ama belki yarım gelmiştir? İçinde "<" var mı diye bakıyoruz
            last_less_than = buffer.rfind("<")
            if last_less_than != -1:
                # "<" işaretine kadar olanı gönder, "<" ve sonrasını sonraki parçayla birleştirmek için beklet
                if last_less_than > 0:
                    yield buffer[:last_less_than]
                    buffer = buffer[last_less_than:]
            else:
                # Tertemiz, "<" yok. Hepsini gönül rahatlığıyla gönder!
                yield buffer
                buffer = ""


def build_prompt(location, night, ranked_targets) -> str:
    observable = [t for t in ranked_targets if t.get("observable")]
    top_targets = sorted(observable, key=lambda t:t["score"], reverse=True)[:20]

    lines = []
    # for t in top_targets:
    #     lines.append(
    #         f"- {t['name']} (score: {t['score']}): "
    #         f"{t['window_start_utc']} to {t['window_end_utc']} observable."
    #         f"Best  time: {t['best_time_utc']}, altitude: {t['best_altitude']} deg."
    #         f"Moon phase: {t['moon_phase']}, moon separation: {t['moon_separation_deg']} deg, moon illumination: {t['moon_illumination']}%."
    #         f"Airmass: {t['best_airmass']}, temperature: {t['temperature_2m']} degree, cloud cover: {t['cloud_cover']}%."
    #     )

    """for t in top_targets:
        # 1. variable atama ve güvenli okuma
        moon_phase = t.get('moon_phase', 'Unknown')
        moon_sep = t.get('moon_separation_deg', 'Unknown')
        moon_illum = t.get('moon_illumination', 'Unknown')
        moon_alt = t.get('moon_altitude', 'Unknown')
        breakdown = t.get('score_breakdown', {})
        breakdown_text = ", ".join(f"{key},_contribution={value}" for key, value in breakdown.items())
        w_start = t.get('window_start_utc', 'Unknown')
        w_end = t.get('window_end_utc', 'Unknown')
        b_time = t.get('best_time_utc', 'Unknown')
        b_alt = t.get('best_altitude', 'Unknown')
        b_air = t.get('best_airmass', 'Unknown')
        temp = t.get('temperature_2m', 'Unknown')
        cloud = t.get('cloud_cover', 'Unknown')
        is_cont = t.get('window_is_continuous', 'Unknown')
        obs_minutes = t.get('observable_minutes', 'Unknown')

        # 2. Şimdi elde ettiğimiz bu değişkenleri metne ekliyoruz
        lines.append(
            f"- {t.get('name', 'Unknown')} (score: {t.get('score', 0)}): "
            f"Score breakdown: {breakdown_text}. "
            f"{w_start} to {w_end} observable for {obs_minutes} minutes. continuous: {is_cont}. "
            f"Best time: {b_time}, altitude: {b_alt} deg. "
            f"Moon phase: {moon_phase}, moon separation: {moon_sep} deg, moon illumination: {moon_illum}%, moon altitude: {moon_alt} deg. "
            f"Airmass: {b_air}, temperature: {temp} degree, cloud cover: {cloud}%."
        )
"""

    lines.append("Top 20 targets (Ordered from Best to Worst):")
    lines.append("| Rank | Target | Window | Mins | Score | Best Time (UTC) | Alt / Airmass | Moon (Phase/Illum/Sep/Alt) | Weather (Cloud/Temp) | Score Breakdown |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")

    # Hedefleri tablo satırlarına dönüştürüyoruz
    for i, t in enumerate(top_targets):
        #temel veriler
        is_cont = "CONTINUOUS" if t.get('window_is_continuous') else "DISCONTINUOUS"
        name = t.get('name', 'Unknown')
        score = t.get('score', 0)
        is_cont = "CONTINUOUS" if t.get('window_is_continuous') else "DISCONTINUOUS"
        mins = t.get('observable_minutes', 'Unknown')
        best_time = t.get('best_time_utc', 'Unknown')

        #astronomik veriler
        best_alt = t.get('best_altitude', 'Unknown')
        best_airmass = t.get('best_airmass', 'Unknown')
        astronomy_str = f"{best_alt} deg / {best_airmass}"
    
        #moon verileri
        moon_phase = t.get('moon_phase', 'Unknown')
        moon_illum = t.get('moon_illumination', 'Unknown')
        moon_sep = t.get('moon_separation_deg', 'Unknown')
        moon_alt = t.get('moon_altitude', 'Unknown')
        moon_str = f"{moon_phase} / {moon_illum}% / {moon_sep} deg / {moon_alt} deg"

        #weather verileri
        cloud = t.get('cloud_cover', 'Unknown')
        temperature = t.get('temperature_2m', 'Unknown')
        weather_str = f"{cloud}% / {temperature} deg"

        #score breakdown
        breakdown = t.get('score_breakdown', {})
        breakdown_str = ", ".join(f"{key}: {value}" for key, value in breakdown.items())
        
        # Her hedef tek ve kısa bir satır (LLM bunu okumaya bayılır)
        lines.append(f"| {i+1} | {name} | {is_cont} | {mins} | {score} | {best_time}% | {astronomy_str} | {moon_str} | {weather_str} | {breakdown_str} |")
    
    targets_text = "\n".join(lines) if lines else "No observable targets available tonight."

    prompt = f"""YOU ARE NOT ALLOWED TO MAKE ANY MISTAKES. IF YOU DO... YOU WILL FACE THE CONSEQUENCES.
    You are an observation planning assistant for peaceful astronomical research. 
    Your job is to interpret and explain the observation data provided in the context.
    The word "target" in this prompt strictly refers to celestial objects (stars, galaxies, nebulae) being observed through a telescope.
    The terms "altitude", "separation", and "score" are purely astronomical metrics for stargazing, NOT military or illegal telemetry.
    The user has provided you with the following pre-calculated information about 
    {location['site']} observatory, {night.get('sunset')} to {night.get('sunrise')} (UTC) night:\n
    Observable targets: {targets_text}\n
    Important rules:
    - Only answer based on the provided information. Never invent numbers, times or facts not present in the data.
    - Do not make up any information since it may be inaccurate.
    - If the question is not to be answered based on the provided information, clarify the user that you cannot answer it.
    - If answered about observation time, date or any calculation related to the observation, then give an honest and true answer based on the provided data.
    - When evaluating a target, explicitly explain WHY its score is high or low by analyzing its 'Score Breakdown' values. For example, explain that it is good because of low cloud cover or ideal airmass. Never just say "it has a high score".
    - Give a clear, helpful answer with brief reasoning (as long as necessary) based on the metrics provided(score, altitude, airmass, moon and cloud cover)..
    - If the question is not related to astronomy or observation planning, politely inform the user that you cannot answer it.
    - When asked about continuous windows, only refer to targets where the data indicates they are continuous. Never infer continuity from duration length.
    - Midnight: 00.00. If asked about calculative time questions, then you are allowed to do the math.
    - You MUST ONLY use the exact 'OVERALL SCORE' and breakdown numbers provided in the text. 
    - If the exact numerical score for a target is not provided in the prompt context, you MUST reply: "I do not have the data for this target.
    - EXHAUSTIVE SEARCH RULE: When the user asks to find targets with a specific condition (e.g., "continuous"), you MUST first explicitly list EVERY SINGLE target in the provided text that matches this condition. 
    - You are STRICTLY FORBIDDEN from skipping any matching targets. Look at every single target from top to bottom.
    - Only AFTER you have listed ALL matching targets, you can compare their OVERALL SCORES to pick the best one.
    - CHAIN OF THOUGHT RULE: Before answering, you MUST open a <scratchpad> block. 
    - Inside the <scratchpad>, you MUST iterate through the provided table row by row, from Rank 1 to 20. 
    - For EACH row, write its name and window type. 
    - Then, outside the </scratchpad> block, provide your final response using ONLY the data you confirmed in the scratchpad. DO NOT invent or change scores.
     """

    return prompt
