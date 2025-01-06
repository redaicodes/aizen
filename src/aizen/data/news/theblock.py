from playwright.sync_api import sync_playwright
from lxml import html
import logging


class TheBlock():
    def __init__(self, url: str = "https://www.theblock.co", debug_mode=False):
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
        tree = html.fromstring(content)
        cards = tree.xpath(
            '//article[@class="articleCard"]')
        self.logger.info(f"Found {len(cards)} news articles")
        articles = []

        for card in cards:
            headline = card.xpath(
                './/h2[contains(@class, "articleCard__headline")]/span//text()')
            headline = headline[0].strip() if headline else ""

            metadata = card.xpath(
                './/div[contains(@class, "meta__wrapper")]//text()')
            metadata = metadata[0].strip() if metadata else ""

            url = card.xpath(
                './/a[contains(@class,"articleCard__thumbnail")]/@href')
            url = f"{self.url}{url[0].strip()}" if url else ""

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
        max_page_id_to_look = (topk // 10) + 1
        articles = []
        for i in range(0, max_page_id_to_look):
            url = f"{self.url}/latest?start={i*10}"
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
                return page.content()

            except Exception as e:
                self.logger.error(f"Error during scraping: {str(e)}")
                raise
            finally:
                browser.close()
                self.logger.info("Browser closed")

    