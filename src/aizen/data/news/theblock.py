from playwright.sync_api import sync_playwright
from lxml import html
import logging


class TheBlock():
    """
    A web scraper for TheBlock cryptocurrency news website.

    This class provides functionality to fetch and parse the latest news articles
    from TheBlock's website using Playwright for browser automation and lxml for
    HTML parsing.

    Attributes:
        url (str): Base URL of TheBlock website
        logger (logging.Logger): Logger instance for the class
    """

    def __init__(self, url: str = "https://www.theblock.co", debug_mode=False):
        """
        Initialize TheBlock scraper instance.

        Args:
            url (str): Base URL of TheBlock website. Defaults to "https://www.theblock.co"
            debug_mode (bool): Enable debug logging if True. Defaults to False
        """
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

    def parse_latest_news(self, content: str):
        """
        Parse HTML content to extract news article information.

        Args:
            content (str): HTML content of the news page

        Returns:
            list: List of dictionaries containing article information with keys:
                - headline: Article headline text
                - metadata: Article metadata (author, date, etc.)
                - url: Full URL to the article
                - thumbnail: URL of the article's thumbnail image
        """
        tree = html.fromstring(content)

        # Find all article cards on the page
        cards = tree.xpath('//article[@class="articleCard"]')
        self.logger.info(f"Found {len(cards)} news articles")

        articles = []
        for card in cards:
            # Extract headline text
            headline = card.xpath(
                './/h2[contains(@class, "articleCard__headline")]/span//text()')
            headline = headline[0].strip() if headline else ""

            # Extract article metadata (author, date)
            metadata = card.xpath(
                './/div[contains(@class, "meta__wrapper")]//text()')
            metadata = metadata[0].strip() if metadata else ""

            # Extract article URL and make it absolute
            url = card.xpath(
                './/a[contains(@class,"articleCard__thumbnail")]/@href')
            url = f"{self.url}{url[0].strip()}" if url else ""

            # Extract thumbnail image URL
            thumbnail = card.xpath(
                './/a[contains(@class,"articleCard__thumbnail")]/img/@src')
            thumbnail = thumbnail[0].strip() if thumbnail else ""

            articles.append({
                "headline": headline,
                "metadata": metadata,
                "url": url,
                "thumbnail": thumbnail
            })

        return articles

    def get_latest_news(self, topk: int = 20):
        """
        Fetch the latest news articles from TheBlock.

        Args:
            topk (int): Number of articles to fetch. Defaults to 20

        Returns:
            list: List of dictionaries containing article information
        """
        # Calculate number of pages needed based on articles per page (10)
        max_page_id_to_look = (topk // 10) + 1
        articles = []

        # Fetch articles from each page
        for i in range(0, max_page_id_to_look):
            url = f"{self.url}/latest?start={i*10}"
            content = self.get_page_content(url)
            articles += self.parse_latest_news(content)

        return articles[:topk]

    def get_page_content(self, url) -> str:
        """
        Fetch page content using Playwright browser automation.

        Args:
            url (str): URL to fetch content from

        Returns:
            str: HTML content of the page

        Raises:
            Exception: Any error that occurs during page fetching
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
            page.set_default_timeout(120000)  # 120 second timeout

            try:
                self.logger.info(f"Navigating to {url}")
                # Navigate to URL and wait for network idle
                page.goto(url, wait_until="networkidle")

                self.logger.info("Getting final page content")
                return page.content()
            except Exception as e:
                self.logger.error(f"Error during scraping: {str(e)}")
                raise
            finally:
                browser.close()
                self.logger.info("Browser closed")
