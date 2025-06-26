# === Import Required Modules ===
import os          # Provides functions for interacting with the file system (e.g., paths, directories)
import csv         # Used to read from and write to CSV files
import requests    # Simplifies sending HTTP requests (e.g., calling the Deepgram API)
import subprocess  # Allows us to run shell commands (used here to call ffmpeg)

# === CONFIGURATION SECTION ===
# These are the settings you can change to control the script's behavior

API_KEY = ("APICODEHERE")  # Deepgram API Key for authentication
VOICE_MODEL = "aura-2-thalia-en"  # Voice model to use from Deepgram (this one is 'Thalia')
INPUT_CSV = "prompts.csv"         # CSV file that contains the prompts and filenames
OUTPUT_DIR = "output_wav"         # Folder where the final WAV files will be saved

# === PREP: Create the output directory if it doesn't exist ===
# This ensures the script won’t crash if the folder isn’t already there
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === FUNCTION: convert_to_ulaw() ===
# This takes a WAV file and converts it to μ-law format (used by many phone systems)
# using ffmpeg (a powerful audio/video processing tool)
def convert_to_ulaw(input_path, output_path):
    command = [
        "ffmpeg",             # The command-line tool being called
        "-y",                 # Overwrite output file if it already exists
        "-i", input_path,     # Input file (temp WAV)
        "-ar", "8000",        # Sample rate: 8000 Hz (standard for telephony)
        "-ac", "1",           # Audio channels: 1 (mono)
        "-f", "wav",          # Output format: WAV
        "-acodec", "pcm_mulaw",  # Audio codec: μ-law (used in phone systems)
        output_path           # Output file path
    ]
    # Run the command quietly (no console output)
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# === FUNCTION: synthesize_prompt() ===
# This sends a line of text to Deepgram's API and processes the resulting audio
def synthesize_prompt(prompt_text, filename):
    # Build the Deepgram Speak API URL with the desired model and settings
    url = f"https://api.deepgram.com/v1/speak?model={VOICE_MODEL}&encoding=linear16&sample_rate=16000"

    # Define the headers needed for the API request
    headers = {
        "Authorization": f"Token {API_KEY}",         # Pass the API key to authorize the request
        "Content-Type": "application/json"           # Tell the server we're sending JSON
    }

    # Create the JSON payload with the text to synthesize
    payload = {
        "text": prompt_text
    }

    # Send the HTTP POST request to the Deepgram API
    response = requests.post(url, json=payload, headers=headers)

    # === If the request was successful ===
    if response.status_code == 200:
        # Create paths for a temporary WAV file and the final output file
        temp_path = os.path.join(OUTPUT_DIR, f"{filename}_temp.wav")
        final_path = os.path.join(OUTPUT_DIR, f"{filename}.wav")

        # Save the raw audio response to a temporary file
        with open(temp_path, "wb") as f:
            f.write(response.content)

        # Convert that raw file to μ-law format and save it
        convert_to_ulaw(temp_path, final_path)

        # Remove the temporary file after conversion
        os.remove(temp_path)

        # Notify the user
        print(f"[🎧] Saved Studio-ready: {final_path}")
    else:
        # Print an error message if the API call failed
        print(f"[!] Error for {filename}: {response.status_code} - {response.text}")

# === MAIN SCRIPT: Process the CSV file ===
# This opens the CSV file line by line and feeds each entry to the synthesize_prompt() function
with open(INPUT_CSV, "r", encoding="utf-8") as file:
    for line in file:
        # Clean up any leading/trailing whitespace and remove surrounding quotes
        line = line.strip().strip('"')

        # Only process lines that include a comma (to separate filename and prompt)
        if "," in line:
            # Split into two parts: name = filename, text = prompt
            name, text = line.split(",", 1)

            # Send to Deepgram and save the processed WAV
            synthesize_prompt(text.strip(), name.strip())