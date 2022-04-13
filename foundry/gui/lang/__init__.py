import json
import os


STRINGS = {}


def _get_options() -> list:
    options = []
    directory = os.scandir("./foundry/data/lang/")

    for entry in directory:
        if entry.is_file() and entry.name.endswith(".json"):
            file = open(entry.path)
            file_data = json.load(file)
            options.append(tuple((file_data["language"], entry.path)))
            file.close()
    return options


def load(path):
    english_file = open('./foundry/data/lang/english.json')
    new_lang_file = open(path)

    english_data = json.load(english_file)
    new_lang_data = json.load(new_lang_file)

    STRINGS.clear()
    STRINGS.update(english_data)
    STRINGS.update(new_lang_data)

    english_file.close()
    new_lang_file.close()


load("./foundry/data/lang/english.json")
LANGUAGE_OPTIONS = _get_options()
