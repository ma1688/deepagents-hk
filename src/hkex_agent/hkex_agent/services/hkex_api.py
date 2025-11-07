"""HKEX API service for fetching announcement data."""

import json
import re
import ssl
from datetime import datetime
from typing import Any

import httpx


class HKEXAPIService:
    """Service for interacting with HKEX APIs."""

    BASE_URL = "https://www1.hkexnews.hk"
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
    }

    def __init__(self, timeout: int = 30):
        """Initialize HKEX API service.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

    def _clean_html_entities(self, text: str) -> str:
        """Clean HTML entities and Unicode escapes from text.

        Args:
            text: Text to clean.

        Returns:
            Cleaned text.
        """
        if not text:
            return text

        # HTML entities
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")

        # Unicode literal escapes
        text = re.sub(r"\\u003c", "<", text)
        text = re.sub(r"\\u003e", ">", text)
        text = re.sub(r"\\u2013", "-", text)
        text = text.replace("\\u0026", "-")

        # Remove backslash escapes
        text = text.replace("\\\\", "")

        return text

    def _parse_jsonp(self, response_text: str) -> dict[str, Any]:
        """Parse JSONP response.

        Args:
            response_text: JSONP response text.

        Returns:
            Parsed JSON data.
        """
        # Extract JSON from callback(...)
        match = re.search(r"callback\((.*)\)", response_text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        return {}

    def _clean_result_data(self, result_data: str | list) -> list[dict[str, Any]]:
        """Clean and parse result data from API response.

        Args:
            result_data: Raw result data (may be JSON string or list).

        Returns:
            Cleaned list of announcement dictionaries.
        """
        if not result_data:
            return []

        # If it's a string, try to parse it
        if isinstance(result_data, str):
            # Remove JSON string escaping
            result_data = result_data.strip()
            if result_data.startswith('"[') and result_data.endswith(']"'):
                result_data = result_data[1:-1]  # Remove outer quotes
            if result_data.startswith("[") and result_data.endswith("]"):
                try:
                    result_data = json.loads(result_data)
                except json.JSONDecodeError:
                    return []

        if not isinstance(result_data, list):
            return []

        cleaned_results = []
        for item in result_data:
            if isinstance(item, dict):
                cleaned_item = {}
                for key, value in item.items():
                    if isinstance(value, str):
                        cleaned_item[key] = self._clean_html_entities(value)
                    else:
                        cleaned_item[key] = value
                cleaned_results.append(cleaned_item)

        return cleaned_results

    def get_stock_id(self, stock_code: str) -> tuple[str | None, list[dict[str, Any]]]:
        """Get stock ID from stock code.

        Args:
            stock_code: 5-digit stock code (e.g., "00673").

        Returns:
            Tuple of (stock_id, stock_info_list). stock_id is None if not found.
        """
        url = (
            f"{self.BASE_URL}/search/prefix.do?"
            f"callback=callback&lang=ZH&type=A&name={stock_code}"
            f"&market=SEHK&_={int(datetime.now().timestamp() * 1000)}"
        )

        try:
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = client.get(url)
                response.raise_for_status()

                # Parse JSONP response
                data = self._parse_jsonp(response.text)

                stock_info = data.get("stockInfo", [])
                if stock_info and len(stock_info) > 0:
                    stock_id = stock_info[0].get("stockId")
                    return stock_id, stock_info

                return None, []

        except Exception as e:
            return None, [{"error": str(e)}]

    def search_announcements(
        self,
        stock_id: str,
        from_date: str,
        to_date: str,
        title: str | None = None,
        market: str = "SEHK",
        document_type: int = -1,
        row_range: int = 100,
        lang: str = "zh",
    ) -> tuple[str, list[dict[str, Any]]]:
        """Search announcements for a stock.

        Args:
            stock_id: Internal stock ID from get_stock_id().
            from_date: Start date in YYYYMMDD format (e.g., "20250101").
            to_date: End date in YYYYMMDD format (e.g., "20251008").
            title: Search keyword in title (optional).
            market: Market code (default: "SEHK").
            document_type: Document type code (default: -1 for all).
            row_range: Number of results (1-500, default: 100).
            lang: Language code (default: "zh").

        Returns:
            Tuple of (stock_id, list of announcement dictionaries).
        """
        params = {
            "sortDir": "0",
            "sortByOptions": "DateTime",
            "category": "0",
            "market": market,
            "stockId": stock_id,
            "documentType": str(document_type),
            "fromDate": from_date,
            "toDate": to_date,
            "searchType": "0",
            "t1code": "-2",
            "t2Gcode": "-2",
            "t2code": "-2",
            "rowRange": str(row_range),
            "lang": lang,
        }

        if title:
            params["title"] = title

        url = f"{self.BASE_URL}/search/titleSearchServlet.do"

        try:
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = client.get(url, params=params)
                response.raise_for_status()

                result_data = response.json()
                result = result_data.get("result", [])

                # Clean and parse result data
                announcements = self._clean_result_data(result)

                return stock_id, announcements

        except Exception as e:
            return stock_id, [{"error": str(e)}]

    def get_latest_announcements(
        self,
        market: str | None = None,
        stock_code: str | None = None,
        t1_code: str | None = None,
        t2_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get latest announcements from HKEX.

        Args:
            market: Filter by market (SEHK/GEM, optional).
            stock_code: Filter by stock code (optional).
            t1_code: Filter by tier 1 category code (optional).
            t2_code: Filter by tier 2 category code (optional).

        Returns:
            List of announcement dictionaries.
        """
        url = f"{self.BASE_URL}/ncms/json/eds/lcisehk1relsdc_1.json"

        try:
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = client.get(url)
                response.raise_for_status()

                data = response.json()
                news_list = data.get("newsInfoLst", [])

                # Apply filters
                filtered_news = []
                for item in news_list:
                    # Market filter
                    if market and item.get("market") != market:
                        continue

                    # Stock code filter
                    if stock_code:
                        stock_items = item.get("stock", [])
                        stock_codes = [s.get("sc", "") for s in stock_items]
                        if stock_code not in stock_codes:
                            continue

                    # Category filters
                    if t1_code and item.get("t1Code") != t1_code:
                        if item.get("t1Code") != "NaN":
                            continue

                    if t2_code and item.get("t2Code") != t2_code:
                        if item.get("t2Code") != "NaN":
                            continue

                    filtered_news.append(item)

                return filtered_news

        except Exception as e:
            return [{"error": str(e)}]

    def get_categories(
        self, category_type: str = "tierone"
    ) -> list[dict[str, Any]]:
        """Get category data from HKEX.

        Args:
            category_type: Category type - "doc", "tierone", "tiertwo", "tiertwogrp".

        Returns:
            List of category dictionaries.
        """
        category_files = {
            "doc": "doc_c.json",
            "tierone": "tierone_c.json",
            "tiertwo": "tiertwo_c.json",
            "tiertwogrp": "tiertwogrp_c.json",
        }

        filename = category_files.get(category_type, "tierone_c.json")
        url = f"{self.BASE_URL}/ncms/script/eds/{filename}"

        try:
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = client.get(url)
                response.raise_for_status()

                categories = response.json()
                return categories if isinstance(categories, list) else []

        except Exception as e:
            return [{"error": str(e)}]

    def parse_date_time(self, date_time_str: str) -> tuple[str, str]:
        """Parse date time string from API response.

        Args:
            date_time_str: Date time string in format "dd/mm/yyyy HH:MM".

        Returns:
            Tuple of (date_str in YYYY-MM-DD format, time_str in HH:MM format).
        """
        try:
            # Parse "dd/mm/yyyy HH:MM" format
            dt = datetime.strptime(date_time_str.split()[0], "%d/%m/%Y")
            date_str = dt.strftime("%Y-%m-%d")
            time_str = date_time_str.split()[1] if " " in date_time_str else ""
            return date_str, time_str
        except Exception:
            return "", ""

