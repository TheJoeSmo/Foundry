import os
import json


def _get_options() -> list:
    options = []
    directory = os.scandir('./foundry/data/lang/')

    for entry in directory:
        if entry.is_file() and entry.name.endswith(".json"):
            file = open(entry.path)
            file_data = json.load(file)
            options.append(tuple((file_data['language'], entry.path)))
            file.close
    return options


LANGUAGE_OPTIONS = _get_options()
