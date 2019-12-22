from __future__ import annotations

import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Union
from urllib.parse import urlparse

import requests

from data.exceptions import InvalidJSON, InvalidCSV

_logger = logging.getLogger(__name__)


@dataclass
class Data:
    name: str


class DataList(List):
    def __init__(self):
        super(DataList, self).__init__()
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_from(self, file: str) -> bool:
        self._logger.info("Try to load {}".format(self.__class__.__name__))

        try:
            # Check if the resource is remote
            if bool(urlparse(file).scheme):
                # Load the remote json
                raw = requests.get(file).text

            else:
                # Open the file and load it as json
                with open(file, 'r') as f:
                    raw = f.read()

        except FileNotFoundError:
            self._logger.warning("Failed to load the list: file not found")
            return False
        except requests.exceptions.ConnectionError:
            self._logger.warning("Failed to load the list: an HTTP error occurred")
            return False

        try:
            self._load_json(raw)
            self._is_loaded = True
        except (InvalidJSON, NotImplementedError):
            pass

        try:
            self._load_csv(raw)
            self._is_loaded = True
        except (InvalidCSV, NotImplementedError):
            pass

        if not self.is_loaded:
            self._logger.warning("The file is in a wrong format")
            return False

        self._logger.debug(self)

        self._logger.info("{} is loaded with {} entities".format(self.__class__.__name__, len(self)))

        return True

    def find(self, name: str, minimal_value: float = 0.4) -> Union[Data, None]:
        if not self.is_loaded:
            return None

        self._logger.debug("Try to find a candidate for '{}'".format(name))
        # Compare the boss_name with each boss in the list and find the most similar

        values = map(lambda x: (x, SequenceMatcher(None, name.lower(), x.name.lower()).ratio()), self)

        value = max(values, key=lambda x: x[1])

        if value[1] >= minimal_value:
            self._logger.debug("Found '{}' with confidence {:.3f}".format(value[0].name, value[1]))
            return value[0]
        else:
            self._logger.debug("No candidate found")
            return None

    def _load_json(self, raw):
        raise NotImplementedError

    def _load_csv(self, raw):
        raise NotImplementedError

    @property
    def _logger(self):
        return _logger
