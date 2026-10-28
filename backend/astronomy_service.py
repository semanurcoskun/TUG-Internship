import json
import csv
import io
from pathlib import Path
from astropy.coordinates import SkyCoord
from astropy import units as u

TARGETS_FILE = Path(__file__).parent /"targets.json"

def load_targets():
    try:
        if not TARGETS_FILE.exists():
            return {"error": "targets.json file not found."}

        with open(TARGETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        return {"error": f"Error loading targets.json: {str(e)}"}

def get_target_coordinates(target_id: str):
    targets = load_targets()
    if isinstance(targets, dict) and "error" in targets:
        return targets #targets.json yoksa

    for target in targets: 
        if target.get("id").upper() == target_id.upper():
            try:
                coord = SkyCoord(target["ra"], target["dec"], unit=(u.deg, u.deg), frame="icrs")
                return {
                    "id": target["id"],
                    "name": target["name"],
                    "ra_deg": coord.ra.degree, #right ascension in degrees
                    "dec_deg": coord.dec.degree, #declination in degrees
                }
            except Exception as e:
                return {"error": f"Error processing target '{target_id}': {str(e)}"}

    return {"error": f"Target with ID '{target_id}' not found."}

def parse_targets_file(filename: str, content: bytes):
    lower_name = filename.lower()
    if lower_name.endswith(".json"):
        try:
            data = json.loads(content.decode("utf-8"))
            if not isinstance(data, list):
                return {"error": "JSON file must contain a list of targets."}
            return data
        except Exception as e:
            return {"error": f"Error parsing JSON file: {str(e)}"}

    elif lower_name.endswith(".csv"):
        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            targets = list(reader)
            required_fields = {"id", "name", "ra", "dec"}
            if targets and not required_fields.issubset(targets[0].keys()):
                return {"error": f"CSV file must contain the following columns: {required_fields}"}
            return targets
        except Exception as e:
            return {"error": f"CSV parsing error: {str(e)}"}
    else:
        return {"error": "Unsupported file format. Please upload a JSON or CSV file."}