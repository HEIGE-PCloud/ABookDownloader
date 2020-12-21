import json
from json.decoder import JSONDecodeError
import logging


class Settings(object):
    def __init__(self, path):

        self.path = path
        self.settings = {}
        self.DEFAULT_SETTINGS = {
            'download_path': './Downloads/',
            'debug': False,
            'proxies': None,
            'auto_login': False,
            'first_launch': True
            }

        self.read_settings_from_file()

    def __getitem__(self, index):
        return self.settings[index]

    def __setitem__(self, index, value):
        self.settings[index] = value
        self.save_settings_to_file()

    def read_settings_from_file(self):

        # Try to load settings from file
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                self.settings = json.load(file)

        # If fail to operate the local file, or the json format is broken
        # then create a new settings file through default settings
        except JSONDecodeError:

            logging.error("Fail to open setting file, create a new one.")

            self.settings = self.DEFAULT_SETTINGS
            self.save_settings_to_file()

        # Check items in settings, and refresh the local file
        for item in self.DEFAULT_SETTINGS:
            if item not in self.settings:
                self.settings[item] = self.DEFAULT_SETTINGS[item]
                self.save_settings_to_file()

        logging.info("Settings loaded.")
        logging.debug(self.settings)

    def save_settings_to_file(self):

        # Open file path and save settings to file
        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(self.settings, file, ensure_ascii=False, indent=4)

        logging.info("Settings saved.")
