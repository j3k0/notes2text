import os
import sys
from api_handlers import GroqHandler
import logging
from dotenv import load_dotenv
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Constants
TMP_DIR = os.getenv('TMP_DIR', 'tmp')
YEAR_PATTERN = os.getenv('YEAR_PATTERN', '2024')
LANGUAGE_HINT = os.getenv('LANGUAGE_HINT', 'fr')

def split_by_year(input_file, min_words=200):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content by years
    entries = content.split(YEAR_PATTERN)
    
    # Create tmp directory if it doesn't exist
    os.makedirs(TMP_DIR, exist_ok=True)
    
    split_files = []
    current_content = ""
    
    # for each entry
    for entry in entries:
        # Add the year to the start of the next entry
        current_content += YEAR_PATTERN + entry
        
        if len(current_content.split()) >= min_words:
            filename = f"{TMP_DIR}/entry_{len(split_files) + 1}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(current_content.strip())
            split_files.append(filename)
            current_content = ""
    
    # Write the last file if there's remaining content
    if current_content:
        filename = f"{TMP_DIR}/entry_{len(split_files) + 1}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(current_content.strip())
        split_files.append(filename)
    
    return split_files

def clean_entry(entry_file, groq_handler, language=LANGUAGE_HINT):
    with open(entry_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    prompt = f"""Here is the output from an OCR software, scanning journal entries.
It's messy. Can you fix it as best as you can, make it well formatted, pure text, restore broken
sentences and words. Just answer with the final text corrected. Thanks. If a sentence is non-sensical,
ignore it (or make it sensical if you can). Make sure sentences are on a single line.

Language Hint: {language}

A bit of help with some personal words: Théa, Hallat, Triominos, Souad

{content}

PLEASE ONLY RESPOND WITH THE CORRECTED TEXT. NO OTHER TEXT.
"""

    response = groq_handler._make_request(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000
    )

    return response

def main():
    parser = argparse.ArgumentParser(description="Clean up OCR-scanned journal entries.")
    parser.add_argument("input_file", help="Path to the input file containing OCR-scanned journal entries.")
    parser.add_argument("--output", help="Path to the output file. If not specified, a default name will be used.")
    args = parser.parse_args()

    # Get environment variables
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL')
    
    if not api_key or not model:
        logging.error("GROQ_API_KEY and GROQ_MODEL must be set in the .env file")
        sys.exit(1)

    # Initialize GroqHandler
    groq_handler = GroqHandler(api_key, model)

    # Get the input file from command line argument
    input_file = args.input_file

    # Generate output file name
    if args.output:
        output_file = args.output
    else:
        input_filename = os.path.basename(input_file)
        name, ext = os.path.splitext(input_filename)
        output_file = f"{name}_cleaned_up{ext}"

    # Split the input file
    logging.info("Splitting input file by years...")
    split_files = split_by_year(input_file)

    # Process each split file
    cleaned_entries = []
    for file in split_files:
        logging.info(f"Cleaning entry: {file}")
        cleaned_entry = clean_entry(file, groq_handler, language=LANGUAGE_HINT)
        cleaned_entries.append(cleaned_entry)

    # Combine cleaned entries
    logging.info("Combining cleaned entries...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(cleaned_entries))

    # Clean up tmp directory
    for file in split_files:
        os.remove(file)
    os.rmdir(TMP_DIR)

    logging.info(f"Cleanup complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()