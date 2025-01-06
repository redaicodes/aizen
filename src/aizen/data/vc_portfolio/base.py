import logging
from abc import ABC, abstractmethod
from typing import Dict


class BaseVCParser(ABC):
    def __init__(self, url: str, debug_mode: bool = False) -> None:
        self.url = url
        # Initialize the logger for the current class
        self.logger = logging.getLogger(self.__class__.__name__)

        # Prevent multiple handlers being added if already set
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Set logging level based on debug_mode
        self.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        self.logger.debug("Debug mode enabled.") if debug_mode else self.logger.info(
            "Logger initialized.")

    @abstractmethod
    def get_page_content(self) -> str:
        pass

    @abstractmethod
    def parse_company_cards(self, content: str) -> list:
        pass

    @abstractmethod
    def scrape(self) -> Dict:
        pass
