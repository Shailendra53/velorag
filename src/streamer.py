import os
import json
import time
import random
from dotenv import load_dotenv

load_dotenv()

def prepare_data_input_dir():
    input_dir = os.getenv("DATA_INPUT_DIR")
    if not input_dir:
        raise ValueError("DATA_INPUT_DIR environment variable not set.")
    os.makedirs(input_dir, exist_ok=True)
    return input_dir

# Ensure the input directory exists
INPUT_DIR = prepare_data_input_dir()

# Prepare dataset.
def prepare_news_headlines():
    mock_headlines_file = os.getenv("MOCK_HEADLINES_FILE")
    if not mock_headlines_file:
        raise ValueError("MOCK_HEADLINES_FILE environment variable not set.")

    with open(mock_headlines_file, "r") as f:
        return [line.strip() for line in f if line.strip()]

# Read mock financial headlines from a file and store them in a list.
HEADLINES = prepare_news_headlines()

def spawn_news_alert(counter):
    headline = random.choice(HEADLINES)
    payload = {
        "id": counter,
        "timestamp": time.time(),
        "headline": headline,
        "source": "REUTERS_MOCK"
    }
    
    # Write to a temporary file first, then rename it.
    # This prevents the C++ engine from reading a partially written file!
    filename = f"news_{counter}.json"
    temp_path = os.path.join(INPUT_DIR, f".tmp_{filename}")
    final_path = os.path.join(INPUT_DIR, filename)
    
    with open(temp_path, "w") as f:
        json.dump(payload, f)
        
    os.rename(temp_path, final_path)
    print(f"[Python Streamer] Spammed: {headline}")

if __name__ == "__main__":
    print("Starting financial news stream... Press Ctrl+C to stop.")
    count = 0
    try:
        while True:
            spawn_news_alert(count)
            count += 1
            time.sleep(2.0)  # Generates a new headline every 2 seconds
    except KeyboardInterrupt:
        print("\nStreamer stopped.")
