import json
from pathlib import Path
from schemas import SurveyRequest

DATA_DIR = Path("data")
SURVEY_FILE = DATA_DIR / "survey_results.json"

def save_survey(survey: SurveyRequest):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    survey_dict = survey.dict()

    if SURVEY_FILE.exists():
        with open(SURVEY_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(survey_dict)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        with open(SURVEY_FILE, "w", encoding="utf-8") as f:
            json.dump([survey_dict], f, ensure_ascii=False, indent=2)

