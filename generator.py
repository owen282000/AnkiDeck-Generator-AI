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

# Set the GPT-4o model
MODEL = "gpt-4o"

# Function to check if the API key is default (not set)
def check_api_key(api_key: str):
    """
    Check if the API key is provided, else exit.
    
    Args:
        api_key (str): The OpenAI API key.
    """
    if api_key == 'openai_api_key':
        print("Error: Default API key found. Please provide a valid OpenAI API key.")
        sys.exit(1)

def parse_input_file(input_file: str, verbose: bool = False) -> List[str]:
    """
    Reads the input file and capitalizes each word/phrase.
    
    Args:
        input_file (str): Path to the input text file.
        verbose (bool): Whether to print debug information.
        
    Returns:
        list: A list of capitalized words/phrases from the input file.
    """
    items: List[str] = []
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip().capitalize()  # Capitalize each word
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

def is_valid_format(result: str, verbose: bool = False) -> bool:
    """
    Check if the generated result follows the format: 'Source sentence (Target sentence) (Target word)'.
    
    Args:
        result (str): The generated result to validate.
        verbose (bool): Whether to print debug information.
        
    Returns:
        bool: True if the result is in the expected format, otherwise False.
    """
    # First check for proper parentheses balance
    if result.count('(') != 2 or result.count(')') != 2:
        if verbose:
            print(f"Invalid result format: {result}")
        return False
    matches = re.findall(r'\(([^)]+)\)', result)
    if len(matches) == 2:
        if verbose:
            print(f"Valid result format: {result}")
        return True
    if verbose:
        print(f"Invalid result format: {result}")
    return False

def parse_generated_response(result: str, verbose: bool = False) -> (str, str, str):
    """
    Extract the source sentence, target sentence, and target word from the generated result.
    
    Args:
        result (str): The generated result in the format: 'Source sentence (Target sentence) (Target word)'.
    
    Returns:
        tuple: source_sentence, target_sentence, target_word
    """
    try:
        # Clean the source sentence by removing unwanted phrases
        source_sentence = result.split('(')[0].strip()
        target_sentence, target_word = re.findall(r'\(([^)]+)\)', result)
        
        # Remove any text that says "vertaalt naar", "hier is een voorbeeldzin", etc.
        source_sentence = re.sub(r"vertaalt naar.*\n*.*voorbeeldzin.*", "", source_sentence).strip()
        if verbose:
            print(f"Cleaned source sentence: {source_sentence}")
        
        # Ensure the target word includes "De" or "Het" when necessary
        if not target_word.istitle() and "de" not in target_word.lower() and "het" not in target_word.lower():
            target_word = f"De {target_word}"
        
        return source_sentence, target_sentence.strip(), target_word.strip()
    
    except Exception as e:
        if verbose:
            print(f"Error parsing result: {e}")
        return "Parsing error", "Parsing error", "Parsing error"


def get_word_translation_and_example(word: str, api_key: str, source_language: str, target_language: str, proficiency: str, verbose: bool = False, retries: int = 3) -> str:
    """
    Uses GPT-4o to get a word translation and generate an example sentence.
    
    Args:
        word (str): The word/phrase to translate and generate an example for.
        api_key (str): The OpenAI API key.
        source_language (str): The source language.
        target_language (str): The target language.
        proficiency (str): The proficiency level of the example sentence.
        verbose (bool): Whether to print debug information.
        retries (int): Number of retries in case of failure.
        
    Returns:
        str: The generated result with translation and example sentence.
    """
    client = OpenAI(api_key=api_key)
    for attempt in range(retries):
        try:
            if verbose:
                print(f"Translating word '{word}' from {source_language} to {target_language}...")

            # Prompt to generate translation and example
            prompt = (f"Translate the phrase or word '{word}' from {source_language} to {target_language}. "
                    f"Generate an example sentence in {source_language} at a {proficiency} level that appropriately uses this phrase or word in context. "
                    f"Provide the translation in the following format: '{source_language} sentence ({target_language} sentence) ({target_language} word/phrase)'. "
                    f"Ensure that all articles (like 'the', 'a', or their equivalents in {target_language}) are only included when required by the grammar of {target_language}. "
                    f"For uncountable nouns or proper names, omit articles. "
                    f"Ensure proper capitalization for both the {target_language} sentence and the {target_language} word/phrase. "
                    f"Do not add unnecessary articles or explanations in the output. "
                    f"Handle multi-word expressions like full phrases (e.g., 'Vosotros sois') as a complete entity rather than translating individual words. "
                    f"To be clear, the final output should follow this format exactly: "
                    f"'{source_language} sentence ({target_language} sentence) ({target_language} word/phrase)', with no additional information or explanations.")


            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            result = response.choices[0].message.content.strip()

            if is_valid_format(result, verbose):
                return result
            else:
                if verbose:
                    print(f"Invalid format detected, retrying... (Attempt {attempt + 1})")
        
        except RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Rate limit exceeded. Skipping translation and example for '{word}'.")
                return "Translation and example not available."

    return "Translation and example not available."

def create_anki_deck(items: List[str], api_key: str, source_language: str, target_language: str, deck_name: str, proficiency: str, verbose: bool = False) -> genanki.Deck:
    """
    Creates an Anki deck with translated words, target language, and example sentences.
    
    Args:
        items (list): List of words/phrases to process.
        api_key (str): The OpenAI API key.
        source_language (str): The source language.
        target_language (str): The target language.
        deck_name (str): The name of the Anki deck to create.
        proficiency (str): The proficiency level for the example sentence.
        verbose (bool): Whether to print debug information.
        
    Returns:
        genanki.Deck: The generated Anki deck.
    """
    deck_id = random.randint(1, 1 << 30)
    model_id = random.randint(1, 1 << 30)

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
        
        # Get both translation and example sentence
        translation_and_example = get_word_translation_and_example(item, api_key, source_language, target_language, proficiency, verbose)
        
        source_sentence, target_sentence, target_word_translation = parse_generated_response(translation_and_example, verbose)
        
        if verbose:
            print(f"Source word: {item}")
            print(f"Target word: {target_word_translation}")
            print(f"Source sentence: {source_sentence}")
            print(f"Target sentence: {target_sentence}")

        # Add the note to the Anki deck
        note = genanki.Note(
            model=model,
            fields=[item, target_word_translation, source_sentence, target_sentence]
        )
        deck.add_note(note)
        if verbose:
            print(f"Added note to deck for '{item}'.")

    total_elapsed_time = time.time() - total_start_time
    if verbose:
        print(f"\nTotal time for processing all items: {total_elapsed_time:.2f} seconds")

    return deck

def main(input_file: str, deck_name: str, output_file: str, api_key: str, source_language: str, target_language: str, proficiency: str, verbose: bool = False) -> None:
    """
    Main function to generate the Anki deck.
    
    Args:
        input_file (str): Path to the input text file.
        deck_name (str): Name of the Anki deck to generate.
        output_file (str): Path to the output .apkg file.
        api_key (str): The OpenAI API key.
        source_language (str): The source language.
        target_language (str): The target language.
        proficiency (str): The proficiency level for the example sentences.
        verbose (bool): Whether to print debug information.
    """
    check_api_key(api_key)
    
    if verbose:
        print(f"Starting to create Anki deck: {deck_name}")
    
    # Parse the input items and create the Anki deck
    items = parse_input_file(input_file, verbose)
    deck = create_anki_deck(items, api_key, source_language, target_language, deck_name, proficiency, verbose)
    
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
    parser.add_argument('--target_language', type=str, help="Target language", default=config['settings'].get('target_language', 'Dutch'))
    parser.add_argument('--proficiency', type=str, help="Proficiency level for example sentence (e.g., Beginner, Advanced, Expert)", default=config['settings'].get('proficiency', 'Beginner'))
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    
    # Parse arguments and run the main function
    args = parser.parse_args()
    main(args.input_file, args.deck_name, args.output_file, args.api_key, args.source_language, args.target_language, args.proficiency, args.verbose)
