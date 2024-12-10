from openai import OpenAI
import re
import json
import datetime


client = OpenAI(
    api_key="Your OpenAI Token"
)
def load_chat_history(chat_history_file):
    try:
        with open(chat_history_file, "r") as file:
            raw_history = file.read().strip()

        parsed_history = []
        conversations = raw_history.split("--------------------------------------------------")

        for conversation in conversations:
            lines = conversation.strip().split("\n")
            if len(lines) >= 2:
                user_line = lines[0].replace("User: ", "").strip()
                gpt_line = lines[1].replace("GPT: ", "").strip()
                parsed_history.append({"role": "user", "content": user_line})
                parsed_history.append({"role": "assistant", "content": gpt_line})

        return parsed_history
    except FileNotFoundError:
        print(f"Error: {chat_history_file} not found. Returning empty list.")
        return []
    except Exception as e:
        print(f"An error occurred while loading chat history: {e}")
        return []

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

def load_json(file_path):
    """Load schedule data from a JSON file."""
    try:
        with open(file_path, "r") as file:
            data = file.read().strip()
            return json.loads(data)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}")
        return {}


def save_json(file_path, data):
    """Save schedule data to a JSON file."""
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"An error occurred while saving to {file_path}: {e}")

def save_chat_history(file_path, user_input, gpt_response):
    try:
        with open(file_path, "a") as file:
            file.write(f"User: {user_input}\n")
            file.write(f"GPT: {gpt_response}\n")
            file.write("-" * 50 + "\n")
    except Exception as e:
        print(f"An error occurred while saving chat history: {e}")

def add_am_pm_marker(time_string):

    if "AM" in time_string or "PM" in time_string:
        return time_string
    try:
        hour = int(time_string.split(":")[0])
        if 1 <= hour <= 11:
            return time_string + " AM"
        elif hour == 12 or hour == 0:
            return time_string + " PM"
        else:
            return time_string + " PM"
    except ValueError:
        return time_string


def is_time_in_range(new_time, existing_time_range):


    try:
        new_time = add_am_pm_marker(new_time)

        # Split the time range into start and end times
        start_time, end_time = existing_time_range.split(" - ")
        start_time = add_am_pm_marker(start_time.strip())
        end_time = add_am_pm_marker(end_time.strip())

        # Convert all times to datetime objects for comparison
        new_time_obj = datetime.datetime.strptime(new_time, "%I:%M %p")
        start_time_obj = datetime.datetime.strptime(start_time, "%I:%M %p")
        end_time_obj = datetime.datetime.strptime(end_time, "%I:%M %p")

        # Check if new_time is within the range
        return start_time_obj <= new_time_obj <= end_time_obj
    except Exception as e:
        print(f"Error parsing time: {e}")
        return False

def update_schedule_json(schedule, day, time, activity):

    if not isinstance(schedule, dict):
        raise ValueError(f"Expected schedule to be a dictionary, but got {type(schedule)}")

    # Initialize the day's schedule if it doesn't exist
    if day not in schedule:
        schedule[day] = []

    # Ensure the day's schedule is a list of dictionaries
    if not isinstance(schedule[day], list):
        raise ValueError(f"Expected schedule[{day}] to be a list, but got {type(schedule[day])}")

    # Iterate over the existing schedule for the day
    for entry in schedule[day]:
        # Check if the time matches or is within an existing time range
        if entry.get("time") == time or is_time_in_range(time, entry.get("time", "")):
            # Replace the activity for the matching time or range
            entry["activity"] = activity
            print(f"Updated activity for {day} at {entry['time']}.")
            return schedule

    # If no matching time range is found, add the new activity
    schedule[day].append({"time": time, "activity": activity})
    print(f"Added new activity for {day} at {time}.")
    return schedule



def classify_question_type(question):
    """Classify if the question is an invitation or a normal question."""
    system_role = load_file("systemrole.txt")

    classification_prompt = (
        "Classify the following question as 'Invitation' or 'Normal':\n"
        f"Question: {question}\n"
        "If it is an invitation, extract the time and activity in JSON format, like:\n"
        '{"type": "Invitation", "time": "Tuesday 3pm", "activity": "go to the market"}\n'
        "If it is a normal question, respond with:\n"
        '{"type": "Normal"}'
    )

    # Create a fresh context for classification
    classification_context = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": classification_prompt}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=classification_context
        )
        classification = response.choices[0].message.content.strip()
        return classification
    except Exception as e:
        print("An error occurred while classifying the question:", e)
        return '{"type": "Error"}'

def chat_loop():
    print("Welcome to GPT Chat Application!")
    print("Type your question to ask ChatGPT.")
    print("Type 'history' to view previous chat history.")
    print("Type 'exit' to end the program.")

    system_role = load_file("systemrole.txt")
    chat_history_file = "chat_history.txt"
    schedule_file_path = "John_Lin_Weekly_Schedule.json"
    schedule_content = load_json(schedule_file_path)
    history_file = load_chat_history("chat_history.txt")
    chat_context = [
        {"role": "system", "content": system_role}
    ]
    chat_context.extend(history_file)

    while True:
        question = input("Enter your question (or type 'exit' to quit): ").strip()
        
        if question.lower() == "exit":
            print("Exiting the program. Goodbye!")
            break
        elif question:
            classification = classify_question_type(question)
            print("Classification:", classification)

            if '"type": "Invitation"' in classification:
                # Extract time and activity from GPT's classification
                match = re.search(r'"time": "(.*?)", "activity": "(.*?)"', classification)
                if match:
                    day_time = match.group(1)
                    activity = match.group(2)

                    # Split day and time
                    try:
                        day, time = day_time.split(" ", 1)
                    except ValueError:
                        print("Error: Invalid day_time format from classification.")
                        continue
                    #print(f"Debug: day_time = {day_time}, activity = {activity}")
                    #print(f"Debug: day = {day}, time = {time}")
                    # Ask GPT for final decision
                    decision_prompt = (
                        f"You have been invited to {activity} at {day_time}. "
                        f"The question was: {question}. Would you like to go? "
                        "If you want to go, answer like: 'Yes' and provide additional sentences. "
                        "If you do not want to go, you can reject and provide your response."
                    )
                    chat_context.append({"role": "user", "content": decision_prompt})

                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=chat_context
                        )
                        gpt_response = response.choices[0].message.content.strip()
                        print("GPT Response:", gpt_response)

                        # Update the schedule if GPT agrees
                        if "yes" in gpt_response.lower():
                            schedule_content = update_schedule_json(schedule_content, day, time, activity)
                            save_json(schedule_file_path, schedule_content)
                            print(f"Schedule updated with activity: {activity} at {day} {time}")

                        chat_context.append({"role": "assistant", "content": gpt_response})
                        save_chat_history(chat_history_file, question, gpt_response)
                    except Exception as e:
                        print("An error occurred:", e)
            elif '"type": "Normal"' in classification:
                # Normal question handling
                chat_context.append({"role": "user", "content": question})
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=chat_context
                    )
                    gpt_response = response.choices[0].message.content.strip()
                    print("GPT Response:", gpt_response)

                    chat_context.append({"role": "assistant", "content": gpt_response})
                    save_chat_history(chat_history_file, question, gpt_response)
                except Exception as e:
                    print("An error occurred:", e)
            else:
                print("An unexpected classification occurred.")
        else:
            print("Please enter a valid question.")

if __name__ == "__main__":
    chat_loop()