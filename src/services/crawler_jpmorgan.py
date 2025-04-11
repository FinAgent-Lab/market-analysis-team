import requests
from docling.document_converter import DocumentConverter


class CrawlerJPMorgan:
    WEEKLY_RECAP_URL = "https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/insights/market-insights/wmr/weekly_market_recap.pdf"

    def __init__(self):
        self.converter = DocumentConverter()

        pass

    def get_weekly_recap(self):
        response = requests.get(self.WEEKLY_RECAP_URL)
        return response.content

    def get_weekly_recap_markdown(self):
        result = self.converter.convert(self.WEEKLY_RECAP_URL)
        return result.document.export_to_markdown()
