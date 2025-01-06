from aizen.data.vc_portfolio.base import BaseVCParser
from playwright.sync_api import sync_playwright
from lxml import html


class BinanceLabsParser(BaseVCParser):
    def __init__(self, url: str = "https://binancelabs.io/portfolio/", debug_mode=False):
        super().__init__(url, debug_mode)

    def get_page_content(self) -> str:
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
                self.logger.info(f"Navigating to {self.url}")

                # Go to URL with less strict wait condition
                page.goto(self.url, wait_until="networkidle")

                # Get the final page state
                self.logger.info("Getting final page content")
                return page.content()

            except Exception as e:
                self.logger.error(f"Error during scraping: {str(e)}")
                raise
            finally:
                browser.close()
                self.logger.info("Browser closed")

    def parse_company_cards(self, content: str) -> list:
        """Parse company cards from HTML content"""
        tree = html.fromstring(content)
        companies = []

        # Find all organization cards
        cards = tree.xpath(
            '//div[contains(@class,"portfolio_module_portfolio__image__EgbVw")]')
        self.logger.info(f"Found {len(cards)} company cards")
        for card in cards:
            try:
                link_elements = card.xpath('.//a')
                links = {}

                # Extract and print each link's href and text
                for link in link_elements:
                    link_url = link.get('href')
                    link_text = "website"
                    if link_url and link_text:
                        links[link_text] = link_url

                logo_url = card.xpath(
                    './/img/@src')
                logo_url = logo_url[0].strip() if logo_url else ""

                company = {
                    # 'name': name,
                    'links': links,
                    'logo_url': logo_url
                }

                companies.append(company)

            except Exception as e:
                self.logger.error(f"Error parsing company card: {str(e)}")
                continue

        return companies

    def scrape(self):
        """Main scraping method"""
        try:
            # Get page content
            content = self.get_page_content()

            # Parse companies
            companies = self.parse_company_cards(content)

            if not companies:
                self.logger.error("No companies found!")
                return []

            return companies

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return []
