from playwright.sync_api import sync_playwright
from lxml import html
import logging
import time


class Blockworks():
    """
    A web scraper for Blockworks cryptocurrency news website.

    This class provides functionality to fetch and parse the latest news articles
    from Blockworks' website using Playwright for browser automation and lxml for
    HTML parsing. It includes support for infinite scroll pagination.

    Attributes:
        url (str): Base URL of Blockworks website
        num_scrolls (int): Number of times to scroll down for loading more content
        logger (logging.Logger): Logger instance for the class
    """

    def __init__(self, url: str = "https://www.blockworks.co", debug_mode=False, num_scrolls=5):
        """
        Initialize Blockworks scraper instance.

        Args:
            url (str): Base URL of Blockworks website. Defaults to "https://www.blockworks.co"
            debug_mode (bool): Enable debug logging if True. Defaults to False
            num_scrolls (int): Number of scroll operations to perform for loading more content.
                             Defaults to 5
        """
        self.url = url
        self.num_scrolls = num_scrolls

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

    def parse_latest_news(self, content: str):
        """
        Parse HTML content to extract news article information.

        Args:
            content (str): HTML content of the news page

        Returns:
            list: List of dictionaries containing article information with keys:
                - headline: Article headline text
                - description: Article description or summary
                - metadata: Article timestamp in datetime format
                - url: Full URL to the article
                - thumbnail: URL of the article's thumbnail image (currently not implemented)
        """
        tree = html.fromstring(content)

        # Find all article cards in the grid layout
        cards = tree.xpath('//div[contains(@class,"grid")]')
        self.logger.info(f"Found {len(cards)} news articles")
        articles = []

        for card in cards:
            # Extract headline text from font-headline class
            headline = card.xpath(
                './/a[contains(@class, "font-headline")]//text()')
            headline = headline[0].strip() if headline else ""

            # Extract article description
            description = card.xpath(
                './/p[contains(@class, "text-base")]//text()')
            description = description[0].strip() if description else ""

            # Extract article timestamp
            metadata = card.xpath(
                './/time/@datetime')
            metadata = metadata[0].strip() if metadata else ""

            # Extract article URL and make it absolute
            url = card.xpath(
                './/a[contains(@class,"font-headline")]/@href')
            url = f"{self.url}{url[0].strip()}" if url else ""

            # Placeholder for thumbnail URL (to be implemented)
            thumbnail = ""

            articles.append({
                "headline": headline,
                "description": description,
                "metadata": metadata,
                "url": url,
                "thumbnail": thumbnail
            })
        return articles

    def get_latest_news(self, topk: int = 20):
        """
        Fetch the latest news articles from Blockworks.

        Args:
            topk (int): Maximum number of articles to return. Defaults to 20

        Returns:
            list: List of dictionaries containing article information, limited to topk items
        """
        articles = []
        url = f"{self.url}/news"
        content = self.get_page_content(url)
        articles += self.parse_latest_news(content)

        return articles[:topk]

    def get_page_content(self, url) -> str:
        """
        Fetch page content using Playwright browser automation with scroll support.

        This method handles infinite scroll pagination by simulating mouse wheel
        events to load more content. It includes delays between scrolls to allow
        for content loading.

        Args:
            url (str): URL to fetch content from

        Returns:
            str: HTML content of the page after scrolling

        Raises:
            Exception: Any error that occurs during page fetching or scrolling
        """
        with sync_playwright() as p:
            self.logger.info("Launching browser...")
            # Launch browser with security settings
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox']
            )

            # Set up browser context with viewport and user agent
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = context.new_page()
            page.set_default_timeout(30000)  # 120 second timeout

            try:
                self.logger.info(f"Navigating to {url}")
                # Navigate and wait for initial content load
                page.goto(url, wait_until="networkidle")

                self.logger.info("Getting final page content")

                # Perform multiple scroll operations to load more content
                for i in range(3):  # Configurable number of scrolls
                    self.logger.info(f"Scrolling down {i}")
                    page.mouse.wheel(0, 15000)  # Scroll down by 15000 pixels
                    time.sleep(2)  # Wait for content to load

                return page.content()

            except Exception as e:
                self.logger.error(f"Error during scraping: {str(e)}")
                raise
            finally:
                browser.close()
                self.logger.info("Browser closed")
