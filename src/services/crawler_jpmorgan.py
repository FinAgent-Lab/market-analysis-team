import requests


class CrawlerJPMorgan:
    WEEKLY_RECAP_URL = "https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/insights/market-insights/wmr/weekly_market_recap.pdf"

    def __init__(self):
        pass

    def get_weekly_recap(self):
        response = requests.get(self.WEEKLY_RECAP_URL)
        return response.content
