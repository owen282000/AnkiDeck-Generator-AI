# AnkiDeck-Generator-AI
## Anki Deck Generator using OpenAI

This project generates Anki flashcards by leveraging the OpenAI API to translate words from a source language to a target language and generate example sentences. It is designed to help language learners create study decks efficiently by automating translation and sentence creation.

## Why OpenAI?

OpenAI is a crucial part of this project because it handles the translation of words and the generation of example sentences. By integrating the OpenAI API, the application can provide accurate translations and context for language learners. The AI-powered translations and examples are aligned with the target language proficiency level, making it an ideal tool for creating personalized Anki decks.

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Configuration

Unless you specify the flags in the command, you need to configure your OpenAI API key and the source/target languages in a config.ini file. Here's an example of the config.ini structure:

```ini
[openai]
api_key = your_openai_api_key

[settings]
source_language = Spanish
target_language = English
proficiency = Beginner
```

### API Key Security

Ensure you keep your OpenAI API key secure. You can use the `config.ini` file or the `--api_key` flag to load the key, but make sure that the file is excluded from version control by adding it to .gitignore.


## Input File Format

The input file should be a simple text file where each word you want to translate is on a new line. Here's an example:

```txt
amigo
coche
gato
```

## Example Usage

To generate an Anki deck, you can run the script like this:

```bash
python generator.py input.txt "Spanish-English Deck" output.apkg -v
```

### Optional Arguments:
- `--api_key`: Specify the OpenAI API key (overwrites the one in the `config.ini`).
- `--source_language`: The source language for translations (default: Spanish).
- `--target_language`: The target language for translations (default: English).
- `--proficiency`: Set the proficiency level for the generated example sentences (e.g., Beginner, Advanced, Expert) (default: Beginner).
- `--verbose`: Enable detailed logging output.

## Importing into Anki

Once you have generated the `.apkg` file, open Anki, go to `File -> Import`, and select the generated `.apkg` file. Your new flashcards will be available for study with both translations and example sentences.


## Error Handling

If the OpenAI API rate limit is exceeded, the script will retry a few times with exponential backoff. If it fails, it will skip generating the example sentence for that specific word and proceed.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contributing

Feel free to contribute to this project by opening issues or submitting pull requests. Contributions are welcome to improve translations, add features, or optimize performance.

---

_Developed by Owen. Happy learning!_