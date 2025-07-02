import os
import json

AUTOFILL_PATH = os.path.join("data", "autofill.json")
os.makedirs("data", exist_ok=True)


def save_autofill_data(template_id: str, data: dict):
    print(f"[DEBUG] Saving autofill for template ID {template_id}")
    all_data = {}
    if os.path.exists(AUTOFILL_PATH):
        try:
            with open(AUTOFILL_PATH, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load existing autofill.json: {e}")

    all_data[str(template_id)] = data

    try:
        with open(AUTOFILL_PATH, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Autofill saved to {AUTOFILL_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to save autofill data: {e}")


def load_autofill_data(template_id: str) -> dict:
    if not os.path.exists(AUTOFILL_PATH):
        print(f"[DEBUG] Autofill file not found: {AUTOFILL_PATH}")
        return {}

    try:
        with open(AUTOFILL_PATH, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            return all_data.get(str(template_id), {})
    except Exception as e:
        print(f"[ERROR] Failed to load autofill: {e}")
        return {}


def clear_autofill_data(template_id: str):
    if not os.path.exists(AUTOFILL_PATH):
        return

    try:
        with open(AUTOFILL_PATH, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        if str(template_id) in all_data:
            del all_data[str(template_id)]
            with open(AUTOFILL_PATH, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] Cleared autofill for {template_id}")
    except Exception as e:
        print(f"[ERROR] Failed to clear autofill for {template_id}: {e}")
