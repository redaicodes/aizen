from playwright.sync_api import sync_playwright
from lxml import html
import logging
import time


class Blockworks():
    def __init__(self, url: str = "https://www.blockworks.co", debug_mode=False, num_scrolls=5):
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
        tree = html.fromstring(content)
        cards = tree.xpath(
            '//div[contains(@class,"grid")]')
        self.logger.info(f"Found {len(cards)} news articles")
        articles = []

        for card in cards:
            headline = card.xpath(
                './/a[contains(@class, "font-headline")]//text()')
            headline = headline[0].strip() if headline else ""

            description = card.xpath(
                './/p[contains(@class, "text-base")]//text()')
            description = description[0].strip() if description else ""

            metadata = card.xpath(
                './/time/@datetime')
            metadata = metadata[0].strip() if metadata else ""

            url = card.xpath(
                './/a[contains(@class,"font-headline")]/@href')
            url = f"{self.url}{url[0].strip()}" if url else ""

            thumbnail = ""
            # TODO: Get thumbnail
            # thumbnail = thumbnail[0].strip() if thumbnail else ""

            articles.append({
                "headline": headline,
                "description": description,
                "metadata": metadata,
                "url": url,
                "thumbnail": thumbnail
            })
        return articles

    def get_latest_news(self, topk: int = 20):
        articles = []
        url = f"{self.url}/news"
        content = self.get_page_content(url)
        articles += self.parse_latest_news(content)

        return articles[:topk]
    

    def get_page_content(self, url) -> str:
        with sync_playwright() as p:
            self.logger.info("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = context.new_page()
            page.set_default_timeout(120000)  # 120 second timeout

            try:
                # Initial navigation
                self.logger.info(f"Navigating to {url}")

                # Go to URL with less strict wait condition
                page.goto(url, wait_until="networkidle")

                # Get the final page state
                self.logger.info("Getting final page content")

                for i in range(3): #make the range as long as needed
                    self.logger.info(f"Scrollig down {i}")
                    page.mouse.wheel(0, 15000)
                    time.sleep(2)

                return page.content()

            except Exception as e:
                self.logger.error(f"Error during scraping: {str(e)}")
                raise
            finally:
                browser.close()
                self.logger.info("Browser closed")

    