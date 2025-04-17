"""Util that calls Korea Investment & Securities API.

In order to set this up, follow instructions at:
https://apiportal.koreainvestment.com/
"""

import json
import time
from typing import Dict, Optional
import requests

from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator


class HantooStockAPIWrapper(BaseModel):
    """Wrapper for Korea Investment & Securities API."""

    hantoo_app_key: SecretStr
    hantoo_app_secret: SecretStr
    base_url: str = "https://openapi.koreainvestment.com:9443"
    access_token: Optional[str] = None
    token_expire_time: float = 0

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and secret exists in environment."""
        hantoo_app_key = get_from_dict_or_env(
            values, "hantoo_app_key", "HANTOO_APP_KEY"
        )
        hantoo_app_secret = get_from_dict_or_env(
            values, "hantoo_app_secret", "HANTOO_APP_SECRET"
        )
        values["hantoo_app_key"] = hantoo_app_key
        values["hantoo_app_secret"] = hantoo_app_secret

        return values

    def get_access_token(self) -> str:
        """Get OAuth access token."""
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token

        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.hantoo_app_key.get_secret_value(),
            "appsecret": self.hantoo_app_secret.get_secret_value(),
        }

        response = requests.post(url, headers=headers, data=json.dumps(body))
        response_data = response.json()

        if response.status_code == 200:
            self.access_token = response_data.get("access_token")
            expire_in_seconds = response_data.get("expires_in", 86400)
            self.token_expire_time = time.time() + expire_in_seconds
            return self.access_token
        else:
            raise Exception(f"Failed to get access token: {response_data}")

    def make_request(
        self,
        method: str,
        endpoint: str,
        tr_id: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict:
        """Make API request to Korea Investment & Securities API."""
        url = f"{self.base_url}{endpoint}"
        access_token = self.get_access_token()

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": self.hantoo_app_key.get_secret_value(),
            "appsecret": self.hantoo_app_secret.get_secret_value(),
            "tr_id": tr_id,
            "custtype": "P",  # Individual customer type
        }

        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:  # POST
            response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")

        return response.json()

    def get_balance_sheet(self, stock_code: str, div_cls: int = 1) -> Dict:
        """Get balance sheet data.

        Args:
            stock_code: Stock code (e.g., "005930" for Samsung Electronics)
            div_cls: 0 for yearly data, 1 for quarterly data
        """
        endpoint = "/uapi/domestic-stock/v1/finance/balance-sheet"
        tr_id = "FHKST66430100"
        params = {
            "FID_DIV_CLS_CODE": f"{div_cls}",  # 0:year, 1:quarter
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        try:
            return self.make_request("GET", endpoint, tr_id, params)
        except Exception as e:
            return {"error": f"Balance sheet data request failed: {str(e)}"}

    def get_income_statement(self, stock_code: str, div_cls: int = 1) -> Dict:
        """Get income statement data.

        Args:
            stock_code: Stock code (e.g., "005930" for Samsung Electronics)
            div_cls: 0 for yearly data, 1 for quarterly data
        """
        endpoint = "/uapi/domestic-stock/v1/finance/income-statement"
        tr_id = "FHKST66430200"
        params = {
            "FID_DIV_CLS_CODE": f"{div_cls}",  # 0:year, 1:quarter
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        try:
            return self.make_request("GET", endpoint, tr_id, params)
        except Exception as e:
            return {"error": f"Income statement data request failed: {str(e)}"}

    def get_financial_ratios(self, stock_code: str, div_cls: int = 1) -> Dict:
        """Get financial ratios data.

        Args:
            stock_code: Stock code (e.g., "005930" for Samsung Electronics)
            div_cls: 0 for yearly data, 1 for quarterly data
        """
        endpoint = "/uapi/domestic-stock/v1/finance/financial-ratio"
        tr_id = "FHKST66430300"
        params = {
            "FID_DIV_CLS_CODE": f"{div_cls}",  # 0:year, 1:quarter
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        try:
            return self.make_request("GET", endpoint, tr_id, params)
        except Exception as e:
            return {"error": f"Financial ratios request failed: {str(e)}"}

    def get_stock_info(self, stock_code: str) -> Dict:
        """Get basic stock information.

        Args:
            stock_code: Stock code (e.g., "005930" for Samsung Electronics)
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/search-stock-info"
        tr_id = "CTPF1002R"
        params = {
            "PRDT_TYPE_CD": "300",  # 300 for stocks
            "PDNO": stock_code,
        }

        try:
            return self.make_request("GET", endpoint, tr_id, params)
        except Exception as e:
            return {"error": f"Stock info request failed: {str(e)}"}

    def analyze_financial_statements(self, stock_code: str) -> Dict:
        """Analyze financial statements for a stock."""
        result = {"stock_code": stock_code, "timestamp": time.time()}

        # Get basic stock info
        try:
            stock_info = self.get_stock_info(stock_code)
            if "output" in stock_info:
                result["stock_info"] = stock_info["output"]
                result["stock_name"] = stock_info["output"].get("prdt_name", "")
        except Exception as e:
            result["stock_info_error"] = str(e)

        # Balance sheet data
        try:
            balance_sheet = self.get_balance_sheet(stock_code)
            result["balance_sheet"] = balance_sheet.get("output", [])
        except Exception as e:
            result["balance_sheet_error"] = str(e)

        # Income statement data
        try:
            income_statement = self.get_income_statement(stock_code)
            result["income_statement"] = income_statement.get("output", [])
        except Exception as e:
            result["income_statement_error"] = str(e)

        # Financial ratios data
        try:
            financial_ratios = self.get_financial_ratios(stock_code)
            result["financial_ratios"] = financial_ratios.get("output", [])
        except Exception as e:
            result["financial_ratios_error"] = str(e)

        # Add analysis results
        result["analysis"] = self._analyze_financial_data(result)

        return result

    def _analyze_financial_data(self, data: Dict) -> Dict:
        """Analyze financial statement data."""
        analysis = {}

        # Balance sheet analysis
        balance_sheet = data.get("balance_sheet", [])
        if balance_sheet and len(balance_sheet) >= 1:
            try:
                recent = balance_sheet[0]

                # Extract assets, liabilities, equity from the correct field names
                total_assets = float(recent.get("total_aset", 0))
                total_liabilities = float(recent.get("total_lblt", 0))
                total_equity = float(recent.get("total_cptl", 0))

                # Add basic metrics
                analysis["total_assets"] = f"{total_assets:,.2f}"
                analysis["total_liabilities"] = f"{total_liabilities:,.2f}"
                analysis["total_equity"] = f"{total_equity:,.2f}"

                # Liquidity analysis
                current_assets = float(recent.get("cras", 0))
                current_liabilities = float(recent.get("flow_lblt", 0))

                analysis["current_assets"] = f"{current_assets:,.2f}"
                analysis["current_liabilities"] = f"{current_liabilities:,.2f}"

                if current_liabilities > 0:
                    current_ratio = current_assets / current_liabilities
                    analysis["current_ratio"] = f"{current_ratio:.2f}"

                    if current_ratio > 2:
                        analysis["liquidity_evaluation"] = "Excellent liquidity"
                    elif current_ratio > 1.5:
                        analysis["liquidity_evaluation"] = "Good liquidity"
                    elif current_ratio > 1:
                        analysis["liquidity_evaluation"] = "Adequate liquidity"
                    else:
                        analysis["liquidity_evaluation"] = "Potential liquidity risk"

                # Debt ratio
                if total_equity > 0:
                    debt_ratio = (total_liabilities / total_equity) * 100
                    analysis["debt_ratio"] = f"{debt_ratio:.2f}%"

                    if debt_ratio < 50:
                        analysis["debt_evaluation"] = "Very low debt (conservative)"
                    elif debt_ratio < 100:
                        analysis["debt_evaluation"] = "Moderate debt"
                    elif debt_ratio < 200:
                        analysis["debt_evaluation"] = "High debt (aggressive)"
                    else:
                        analysis["debt_evaluation"] = "Very high debt (risky)"
            except Exception as e:
                analysis["balance_sheet_analysis_error"] = str(e)

        # Income statement analysis
        income_statement = data.get("income_statement", [])
        if income_statement and len(income_statement) >= 2:
            try:
                recent = income_statement[0]
                previous = income_statement[1]

                recent_sales = float(recent.get("sale_account", 0))
                recent_op_profit = float(recent.get("bsop_prti", 0))
                recent_net_income = float(recent.get("thtr_ntin", 0))

                previous_sales = float(previous.get("sale_account", 0))
                previous_net_income = float(previous.get("thtr_ntin", 0))

                # Add basic metrics
                analysis["recent_sales"] = f"{recent_sales:,.2f}"
                analysis["recent_operating_profit"] = f"{recent_op_profit:,.2f}"
                analysis["recent_net_income"] = f"{recent_net_income:,.2f}"

                # Calculate growth rates
                if previous_sales > 0:
                    sales_growth = (
                        (recent_sales - previous_sales) / previous_sales
                    ) * 100
                    analysis["sales_growth"] = f"{sales_growth:.2f}%"

                    if sales_growth > 20:
                        analysis["sales_growth_evaluation"] = "Strong sales growth"
                    elif sales_growth > 5:
                        analysis["sales_growth_evaluation"] = "Good sales growth"
                    elif sales_growth > 0:
                        analysis["sales_growth_evaluation"] = "Modest sales growth"
                    else:
                        analysis["sales_growth_evaluation"] = "Declining sales"

                # Operating margin
                if recent_sales > 0:
                    op_margin = (recent_op_profit / recent_sales) * 100
                    analysis["operating_margin"] = f"{op_margin:.2f}%"

                    if op_margin > 15:
                        analysis["profitability_evaluation"] = "Excellent profitability"
                    elif op_margin > 10:
                        analysis["profitability_evaluation"] = "Good profitability"
                    elif op_margin > 5:
                        analysis["profitability_evaluation"] = "Average profitability"
                    else:
                        analysis["profitability_evaluation"] = (
                            "Below average profitability"
                        )

                # Net income growth
                if previous_net_income > 0:
                    net_income_growth = (
                        (recent_net_income - previous_net_income) / previous_net_income
                    ) * 100
                    analysis["net_income_growth"] = f"{net_income_growth:.2f}%"
            except Exception as e:
                analysis["income_statement_analysis_error"] = str(e)

        # Financial ratios analysis
        financial_ratios = data.get("financial_ratios", [])
        if financial_ratios and len(financial_ratios) >= 1:
            try:
                recent = financial_ratios[0]

                roe = float(recent.get("roe_val", 0))
                eps = float(recent.get("eps", 0))
                bps = float(recent.get("bps", 0))
                reserve_rate = recent.get("rsrv_rate", "N/A")
                liability_rate = recent.get("lblt_rate", "N/A")

                # ROE analysis
                analysis["roe"] = f"{roe:.2f}%"

                if roe > 15:
                    analysis["roe_evaluation"] = "Excellent ROE"
                elif roe > 10:
                    analysis["roe_evaluation"] = "Good ROE"
                elif roe > 5:
                    analysis["roe_evaluation"] = "Average ROE"
                else:
                    analysis["roe_evaluation"] = "Below average ROE"

                # Record EPS, BPS
                analysis["eps"] = f"{eps}"
                analysis["bps"] = f"{bps}"
                analysis["reserve_rate"] = reserve_rate
                analysis["liability_rate"] = liability_rate
            except Exception as e:
                analysis["financial_ratios_analysis_error"] = str(e)

        return analysis
