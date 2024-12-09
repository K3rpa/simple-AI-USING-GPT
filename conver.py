import json
def load_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return "You are a helpful assistant."
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}")
        return "You are a helpful assistant."
def text_to_json(schedule_text):
    schedule_json = {}
    lines = schedule_text.splitlines()
    current_day = None

    for line in lines:
        line = line.strip()
        if line.startswith("###"):  # Identify day headers
            current_day = line.replace("###", "").strip()
            schedule_json[current_day] = []
        elif "|" in line and current_day:  # Parse schedule entries
            parts = line.split("|")
            if len(parts) >= 3:
                time = parts[1].strip()
                activity = parts[2].strip()
                schedule_json[current_day].append({"time": time, "activity": activity})

    return schedule_json

def save_json_to_file(data, filename):
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

# Example usage
schedule_text = load_file("John_Lin_Weekly_Schedule.txt")
schedule_json = text_to_json(schedule_text)
save_json_to_file(schedule_json, "John_Lin_Weekly_Schedule.json")
