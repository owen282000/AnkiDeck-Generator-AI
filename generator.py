from typing import List
import configparser
import argparse
import genanki
import random
import time
import re
import sys
from openai import OpenAI, RateLimitError

# Create ConfigParser instance
config = configparser.ConfigParser()

# Read the config from 'config.ini' file
config.read('config.ini')

# Function to check if the API key is default (not set)
def check_api_key(api_key: str):
    if api_key == 'openai_api_key':
        print("Error: Default API key found. Please provide a valid OpenAI API key.")
        sys.exit(1)

def parse_input_file(input_file: str, verbose: bool = False) -> List[str]:
    """
    Reads the input file and parses each line as an item (word/phrase).
    
    Args:
        input_file (str): Path to the input text file.
        verbose (bool): Whether to print debug information.
        
    Returns:
        list: A list of words/phrases from the input file.
    """
    items: List[str] = []
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    items.append(line)
                    if verbose:
                        print(f"Read word/phrase: {line}")
                else:
                    if verbose:
                        print(f"Skipped empty or incorrect line.")
    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return items

def extract_translation_from_example(example_sentence: str, verbose: bool = False) -> str:
    """
    Extracts the target language translation from the example sentence by looking for text inside parentheses.
    
    Args:
        example_sentence (str): The sentence containing both the source and target language versions.
        verbose (bool): Whether to print debug information.
        
    Returns:
        str: The extracted target language translation, or None if not found.
    """
    match = re.search(r'\(([^)]+)\)', example_sentence)
    if match:
        translation = match.group(1).strip()
        if verbose:
            print(f"Extracted translation from example: {translation}")
        return translation
    if verbose:
        print(f"No translation found in the example sentence.")
    return "No translation available"

def get_word_translation(word: str, api_key: str, source_language: str, target_language: str, verbose: bool = False, retries: int = 3) -> str:
    """
    Uses OpenAI to get a target language translation for the provided word in source language.
    
    Args:
        word (str): The word/phrase for which to generate the target language translation.
        api_key (str): The OpenAI API key.
        source_language (str): Source language of the word.
        target_language (str): Target language to translate the word into.
        verbose (bool): Whether to print debug information.
        retries (int): Number of retries if a valid translation is not generated.
        
    Returns:
        str: The target language translation of the word.
    """
    client = OpenAI(api_key=api_key)
    for attempt in range(retries):
        try:
            if verbose:
                print(f"Translating word '{word}' from {source_language} to {target_language}...")

            # Prompt to translate the word from source_language to target_language
            prompt = f"Translate the {source_language} word '{word}' to {target_language}."
            
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=10
            )
            translation = response.choices[0].text.strip()

            if verbose:
                print(f"Translation: {translation}")
            return translation
        
        except RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Rate limit exceeded. Skipping translation for '{word}'.")
                return f"Translation not available."
    
    return "Translation not available."

def get_example_sentence(word: str, api_key: str, source_language: str, target_language: str, verbose: bool = False, retries: int = 3) -> str:
    """
    Uses OpenAI to generate an example sentence for the provided word in the specified language.
    Ensures the sentence is at an appropriate difficulty level.

    Args:
        word (str): The word/phrase for which to generate the example sentence.
        api_key (str): The OpenAI API key.
        source_language (str): The source language.
        target_language (str): The target language.
        verbose (bool): Whether to print debug information.
        retries (int): Number of retries if a valid example sentence is not generated.
        
    Returns:
        str: The generated example sentence with a translation in parentheses.
    """
    client = OpenAI(api_key=api_key)
    start_time = time.time()
    for attempt in range(retries):
        try:
            if verbose:
                print(f"Generating example sentence for '{word}' in {source_language}...")

            # Dynamically use source and target languages
            prompt = (
                f"Generate a simple example sentence for the word '{word}' in {source_language}. "
                f"The sentence should be appropriate for learners studying {source_language}. "
                f"The format must be: '{source_language} sentence. ({target_language} sentence)'."
            )

            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=50
            )
            example_sentence = response.choices[0].text.strip()

            if '(' in example_sentence and ')' in example_sentence:
                elapsed_time = time.time() - start_time
                if verbose:
                    print(f"Example sentence: {example_sentence} (took {elapsed_time:.2f} seconds)")
                return example_sentence
            else:
                if verbose:
                    print(f"No translation found. Retrying... (Attempt {attempt + 1})")

        except RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Rate limit exceeded. Skipping example sentence for '{word}'.")
                return "Example sentence not available due to limit."

    return "Example sentence not available."

def create_anki_deck(items: List[str], api_key: str, source_language: str, target_language: str, deck_name: str, verbose: bool = False) -> genanki.Deck:
    """
    Creates an Anki deck with source and target translations, including example sentences for each word/phrase.
    
    Args:
        items (list): List of words/phrases to process.
        api_key (str): The OpenAI API key.
        source_language (str): The source language.
        target_language (str): The target language.
        deck_name (str): The name of the Anki deck to create.
        verbose (bool): Whether to print debug information.
        
    Returns:
        genanki.Deck: The generated Anki deck.
    """
    deck_id = random.randint(1, 1 << 30)
    model_id = random.randint(1, 1 << 30)

    # Define the Anki model with fields for source, target word translation, and example sentences
    deck = genanki.Deck(
        deck_id=deck_id,
        name=deck_name
    )

    model = genanki.Model(
        model_id=model_id,
        name=f"{source_language}-{target_language}",
        fields=[
            {"name": source_language},
            {"name": target_language},
            {"name": f"ExampleSentence{source_language}"},
            {"name": f"ExampleSentence{target_language}"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": f"{{{{{source_language}}}}}<br><br><i>\"{{{{ExampleSentence{source_language}}}}}\"</i>",
                "afmt": f"{{{{FrontSide}}}}<br><br><hr id=answer><br><br>{{{{{target_language}}}}}<br><br><i>\"{{{{ExampleSentence{target_language}}}}}\"</i>",
            },
            {
                "name": "Card 2",
                "qfmt": f"{{{{{target_language}}}}}<br><br><i>\"{{{{ExampleSentence{target_language}}}}}\"</i>",
                "afmt": f"{{{{FrontSide}}}}<br><br><hr id=answer><br><br>{{{{{source_language}}}}}<br><br><i>\"{{{{ExampleSentence{source_language}}}}}\"</i>",
            },
        ],
        css="""
        .card {
            font-family: arial;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white.
        }
        """
    )

    total_start_time = time.time()

    for item in items:
        if verbose:
            print(f"\nProcessing item: {item}")
        
        # Get the target translation of the source word
        target_word_translation = get_word_translation(item, api_key, source_language, target_language, verbose)
        
        # Generate an example sentence in source language
        example_sentence_source = get_example_sentence(item, api_key, source_language, target_language, verbose)
        
        # Extract the target translation from the example sentence
        target_sentence_translation = extract_translation_from_example(example_sentence_source, verbose)
        
        # Make sure no field is None; replace None with an empty string
        example_sentence_clean_source = example_sentence_source.split('(')[0].strip() if example_sentence_source else ""
        target_sentence_translation = target_sentence_translation if target_sentence_translation else ""
        
        # Add the note to the Anki deck with fields in source, target translation, and example sentences
        note = genanki.Note(
            model=model,
            fields=[item, target_word_translation, example_sentence_clean_source, target_sentence_translation]
        )
        deck.add_note(note)
        if verbose:
            print(f"Added note to deck for '{item}'.")

    total_elapsed_time = time.time() - total_start_time
    if verbose:
        print(f"\nTotal time for processing all items: {total_elapsed_time:.2f} seconds")

    return deck

def main(input_file: str, deck_name: str, output_file: str, api_key: str, source_language: str, target_language: str, verbose: bool = False) -> None:
    """
    Main function to generate the Anki deck by reading input, creating cards, and saving the deck.
    
    Args:
        input_file (str): Path to the input text file.
        deck_name (str): Name of the Anki deck to generate.
        output_file (str): Path to the output .apkg file.
        api_key (str): The OpenAI API key.
        source_language (str): The source language.
        target_language (str): The target language.
        verbose (bool): Whether to print debug information.
    """
    check_api_key(api_key)
    
    if verbose:
        print(f"Starting to create Anki deck: {deck_name}")
    
    # Parse the input items and create the Anki deck
    items = parse_input_file(input_file, verbose)
    deck = create_anki_deck(items, api_key, source_language, target_language, deck_name, verbose)
    
    # Write the deck to the specified output file
    genanki.Package(deck).write_to_file(output_file)
    if verbose:
        print(f"Anki deck '{output_file}' successfully created!")

if __name__ == "__main__":
    # Set up argument parsing for the script
    parser = argparse.ArgumentParser(description="Generate an Anki deck from a text file.")
    parser.add_argument('input_file', type=str, help="Path to the input text file.")
    parser.add_argument('deck_name', type=str, help="Name of the Anki deck to generate.")
    parser.add_argument('output_file', type=str, help="Path to the output .apkg file.")
    parser.add_argument('--api_key', type=str, help="OpenAI API key", default=config['openai'].get('api_key', 'openai_api_key'))
    parser.add_argument('--source_language', type=str, help="Source language", default=config['settings'].get('source_language', 'Spanish'))
    parser.add_argument('--target_language', type=str, help="Target language", default=config['settings'].get('target_language', 'English'))
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    
    # Parse arguments and run the main function
    args = parser.parse_args()
    main(args.input_file, args.deck_name, args.output_file, args.api_key, args.source_language, args.target_language, args.verbose)