"""Professional ESG data retrieval and analysis tool.

Provides comprehensive ESG data analysis including:
- Historical ESG trends with peer comparison
- Data interpolation for missing values
- Monthly trend analysis and performance metrics
"""

import asyncio
import json
import urllib.request
from typing import Dict, Any, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, ConfigDict


class ESGSearchWrapper(BaseModel):
    """Professional ESG data analysis wrapper with comprehensive features."""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    def _get_historical_esg_with_peers(
        self, ticker: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Retrieve historical ESG data with peer comparison from Yahoo Finance ESG Chart API.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Tuple of (combined_dataframe, peer_group_name)
        """
        url = f"https://query2.finance.yahoo.com/v1/finance/esgChart?symbol={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))

            result = data["esgChart"]["result"][0]

            # Company ESG data
            company_df = pd.DataFrame(result["symbolSeries"])
            company_df["Date"] = pd.to_datetime(company_df["timestamp"], unit="s")
            company_df = company_df.set_index("Date")[
                ["esgScore", "environmentScore", "socialScore", "governanceScore"]
            ]

            # Peer group ESG data
            peer_df = pd.DataFrame(result["peerSeries"])
            peer_df["Date"] = pd.to_datetime(peer_df["timestamp"], unit="s")
            peer_df = peer_df.set_index("Date")[
                ["esgScore", "environmentScore", "socialScore", "governanceScore"]
            ]
            peer_df.columns = [
                "peer_esgScore",
                "peer_environmentScore",
                "peer_socialScore",
                "peer_governanceScore",
            ]

            # Combine datasets
            combined_df = company_df.join(peer_df, how="outer")

            # Apply interpolation for missing values
            company_cols = [
                "esgScore",
                "environmentScore",
                "socialScore",
                "governanceScore",
            ]
            peer_cols = [
                "peer_esgScore",
                "peer_environmentScore",
                "peer_socialScore",
                "peer_governanceScore",
            ]

            combined_df[company_cols] = (
                combined_df[company_cols].interpolate(method="time").bfill().ffill()
            )
            combined_df[peer_cols] = (
                combined_df[peer_cols].interpolate(method="time").bfill().ffill()
            )

            combined_df = combined_df.round(2)
            peer_group = result.get("peerGroup", "Unknown")

            return combined_df, peer_group

        except Exception:
            return None, None

    def get_esg_data_by_date(
        self, ticker: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get ESG data for a specific year/month, or latest data if not specified.

        Args:
            ticker: Stock ticker symbol
            year: Target year (optional)
            month: Target month (optional)

        Returns:
            ESG data dictionary for the specified date or latest available
        """
        ticker = ticker.upper()

        try:
            # Get historical data with peers
            combined_df, peer_group = self._get_historical_esg_with_peers(ticker)

            if combined_df is None:
                return {
                    "ticker": ticker,
                    "error": f"Historical ESG data not available for {ticker}",
                }

            # Get monthly data
            monthly_data = combined_df.resample("ME").last()

            if monthly_data.empty:
                return {
                    "ticker": ticker,
                    "error": f"No monthly data available for {ticker}",
                }

            # Find target data
            target_data = None

            if year is not None and month is not None:
                # Search for specific year/month
                target_date = f"{year}-{month:02d}"
                for date, row in monthly_data.iterrows():
                    if date.strftime("%Y-%m") == target_date:
                        target_data = row
                        target_date_str = date.strftime("%Y-%m")
                        break

            # If not found or not specified, use latest data
            if target_data is None:
                target_data = monthly_data.iloc[-1]
                target_date_str = monthly_data.index[-1].strftime("%Y-%m")

            # Calculate performance vs peers
            def get_performance_status(company_score, peer_score):
                if pd.isna(company_score) or pd.isna(peer_score):
                    return "similar"
                diff = abs(company_score - peer_score)
                if diff < 0.5:
                    return "similar"
                return "worse" if company_score > peer_score else "better"

            def get_risk_level(esg_score):
                if pd.isna(esg_score):
                    return "Unknown"
                if esg_score < 10:
                    return "Low"
                elif esg_score < 25:
                    return "Medium"
                else:
                    return "High"

            # Prepare result in the requested format
            result = {
                "ticker": ticker,
                "company_name": f"{ticker} Inc.",  # Simplified company name
                "total_esg_score": {
                    "score": target_data.get("esgScore"),
                    "risk_level": get_risk_level(target_data.get("esgScore")),
                    "industry_average": target_data.get("peer_esgScore"),
                    "vs_industry": get_performance_status(
                        target_data.get("esgScore"), target_data.get("peer_esgScore")
                    ),
                },
                "environment_score": {
                    "score": target_data.get("environmentScore"),
                    "industry_average": target_data.get("peer_environmentScore"),
                    "vs_industry": get_performance_status(
                        target_data.get("environmentScore"),
                        target_data.get("peer_environmentScore"),
                    ),
                },
                "social_score": {
                    "score": target_data.get("socialScore"),
                    "industry_average": target_data.get("peer_socialScore"),
                    "vs_industry": get_performance_status(
                        target_data.get("socialScore"),
                        target_data.get("peer_socialScore"),
                    ),
                },
                "governance_score": {
                    "score": target_data.get("governanceScore"),
                    "industry_average": target_data.get("peer_governanceScore"),
                    "vs_industry": get_performance_status(
                        target_data.get("governanceScore"),
                        target_data.get("peer_governanceScore"),
                    ),
                },
                "rating_year": int(target_date_str.split("-")[0]),
                "rating_month": int(target_date_str.split("-")[1]),
                "peer_group": peer_group,
                "data_source": "Yahoo Finance ESG Chart API",
                "is_latest": year is None or month is None,
            }

            return result

        except Exception as e:
            return {"ticker": ticker, "error": f"ESG data retrieval failed: {str(e)}"}

    async def get_esg_data_by_date_async(
        self, ticker: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Async version of get_esg_data_by_date."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_esg_data_by_date, ticker, year, month
        )

    def get_esg_data_sync(
        self,
        ticker: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Get ESG data for specific date or latest available."""
        return self.get_esg_data_by_date(ticker, year, month)

    async def get_esg_data_async(
        self,
        ticker: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Async version - Get ESG data for specific date or latest available."""
        return await self.get_esg_data_by_date_async(ticker, year, month)
