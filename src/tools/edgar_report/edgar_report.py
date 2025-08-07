import requests
import re
import time
import random
from typing import Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_result,
)
from pydantic import BaseModel, ConfigDict, Field
import sec_edgar_api


class EdgarReporterWrapper(BaseModel):
    """SEC EDGAR 10-K/10-Q report analyzer with comprehensive company lookup"""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    edgar_client: Optional[sec_edgar_api.EdgarClient] = Field(
        default=None, exclude=True
    )
    user_agent: str = Field(default="Pseudo-lab/gomgomcode@gmail.com")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_edgar_client()

    def _initialize_edgar_client(self):
        """SEC EDGAR API 클라이언트 초기화"""
        try:
            self.edgar_client = sec_edgar_api.EdgarClient(user_agent=self.user_agent)
        except Exception as e:
            print(f"EDGAR 클라이언트 초기화 실패: {e}")
            self.edgar_client = None

    def clean_company_name(self, company_name: str) -> str:
        """회사명에서 법인 형태 접미사를 제거하는 함수"""
        suffixes = [
            r"\binc\.?$",
            r"\bincorporated$",
            r"\bcorp\.?$",
            r"\bcorporation$",
            r"\bllc$",
            r"\bllp$",
            r"\blimited$",
            r"\bltd\.?$",
            r"\bco\.?$",
            r"\bcompany$",
            r"\bgroup$",
            r"\bholdings?$",
            r"\benterprise$",
            r"\bsolutions$",
            r"\btechnologies$",
            r"\bservices$",
            r"\bsystems$",
        ]

        cleaned_name = company_name.lower().strip()

        for suffix in suffixes:
            cleaned_name = re.sub(suffix, "", cleaned_name, flags=re.IGNORECASE).strip()

        # 연속된 공백을 하나로 합치기
        cleaned_name = re.sub(r"\s+", " ", cleaned_name)

        return cleaned_name

    def find_company_cik(self, company_name: str) -> Optional[Dict[str, str]]:
        """회사명으로부터 CIK와 티커를 찾는 함수"""
        try:
            # SEC의 회사 검색 API 사용
            search_url = "https://www.sec.gov/files/company_tickers.json"
            headers = {"User-Agent": self.user_agent}

            response = requests.get(search_url, headers=headers)

            if response.status_code == 200:
                companies_data = response.json()

                # 검색어 정리
                company_name_lower = company_name.lower()
                cleaned_search_name = self.clean_company_name(company_name)

                # 1단계: 정확한 일치 확인 (원본 검색어)
                for company_info in companies_data.values():
                    company_title = company_info["title"].lower()
                    ticker = company_info["ticker"].lower()
                    cik = str(company_info["cik_str"]).zfill(10)

                    if (
                        company_name_lower == company_title
                        or company_name_lower == ticker
                    ):
                        return {
                            "cik": cik,
                            "ticker": company_info["ticker"],
                            "company_name": company_info["title"],
                        }

                # 2단계: 정리된 회사명으로 정확한 일치 확인
                for company_info in companies_data.values():
                    company_title = company_info["title"]
                    ticker = company_info["ticker"].lower()
                    cleaned_company_title = self.clean_company_name(company_title)
                    cik = str(company_info["cik_str"]).zfill(10)

                    if (
                        cleaned_search_name == cleaned_company_title
                        or company_name_lower == ticker
                    ):
                        return {
                            "cik": cik,
                            "ticker": company_info["ticker"],
                            "company_name": company_info["title"],
                        }

                # 3단계: 부분 일치 검색
                for key, company_info in companies_data.items():
                    company_title = company_info["title"]
                    cleaned_company_title = self.clean_company_name(company_title)
                    cik = str(company_info["cik_str"]).zfill(10)

                    if (
                        cleaned_search_name in cleaned_company_title
                        or cleaned_company_title in cleaned_search_name
                    ):
                        return {
                            "cik": cik,
                            "ticker": company_info["ticker"],
                            "company_name": company_info["title"],
                        }

                # 4단계: 유사한 회사들 찾기
                similar_companies = []
                search_words = [
                    word for word in cleaned_search_name.split() if len(word) > 2
                ]

                if search_words:
                    for key, company_info in companies_data.items():
                        company_title = company_info["title"]
                        cleaned_company_title = self.clean_company_name(company_title)

                        if all(word in cleaned_company_title for word in search_words):
                            similar_companies.append(
                                {
                                    "cik": str(company_info["cik_str"]).zfill(10),
                                    "ticker": company_info["ticker"],
                                    "company_name": company_info["title"],
                                }
                            )

                    if similar_companies:
                        return similar_companies[0]

            return None

        except Exception as e:
            print(f"회사 검색 중 오류: {e}")
            return None

    @retry(
        retry=(
            retry_if_result(
                lambda x: x.status_code == 429 if hasattr(x, "status_code") else False
            )
        ),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
    )
    def make_request(self, url: str) -> requests.Response:
        """Make a request with retry logic for rate limiting"""
        time.sleep(random.uniform(1, 3))
        response = requests.get(
            url, headers={"User-Agent": self.user_agent}, timeout=30
        )
        return response

    def get_company_filings(self, company_identifier: str) -> Optional[Dict[str, Any]]:
        """회사 식별자로부터 회사 정보와 파일링을 가져오는 함수"""
        if not self.edgar_client:
            return None

        company_info = None

        # CIK가 숫자인지 확인
        if company_identifier.replace("-", "").isdigit():
            cik = company_identifier.replace("-", "").zfill(10)
            company_info = {"cik": cik}
        else:
            # 회사명 또는 티커로 CIK 찾기
            company_info = self.find_company_cik(company_identifier)

            if not company_info:
                return None

        try:
            # SEC EDGAR API로 회사 정보 가져오기
            cik = company_info["cik"]
            submissions = self.edgar_client.get_submissions(cik=cik)

            # 최근 파일링들 확인
            recent_filings = submissions["filings"]["recent"]

            return {
                "company_info": submissions,
                "recent_filings": recent_filings,
                "cik": cik,
            }

        except Exception as e:
            print(f"회사 정보 조회 중 오류: {e}")
            return None

    def get_10k_document_content(
        self, cik: str, accession_number: str
    ) -> Optional[str]:
        """10-K 문서 내용을 가져오는 함수"""
        try:
            accession_clean = accession_number.replace("-", "")
            base_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}"
            )

            # 가능한 파일명들
            possible_filenames = [
                f"{accession_number}.txt",
                "form10k.htm",
                f"{accession_number}-10-k.htm",
            ]

            for filename in possible_filenames:
                filing_url = f"{base_url}/{filename}"

                try:
                    response = self.make_request(filing_url)

                    if response.status_code == 200:
                        return response.text

                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"10-K 문서 조회 중 오류: {e}")
            return None

    def clean_html(self, html_content: str) -> str:
        """HTML 태그를 제거하고 텍스트를 정리합니다."""
        from bs4 import BeautifulSoup

        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(html_content, "html.parser")

        # 불필요한 태그 제거 (e.g., script, style)
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # 텍스트 추출
        text = soup.get_text()

        # 여러 줄바꿈과 공백을 정리
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def extract_10k_items(self, document_content: str) -> Dict[str, str]:
        """10-K 문서에서 주요 항목(Item)들을 추출합니다."""

        # HTML을 정리하여 텍스트만 추출
        text_content = self.clean_html(document_content)

        # 개선된 유연한 정규식 패턴 정의
        items_to_extract = {
            "Item 1. Business": r"Item\s+1\.?\s*Business",
            "Item 1A. Risk Factors": r"Item\s+1A\.?\s*Risk\s*Factors",
            "Item 7. Management's Discussion and Analysis": [
                r"Item\s+7\.?\s*Management['']*s?\s*Discussion\s*and\s*Analysis",
                r"Item\s+7\.?\s*Management['']*s?\s*Discussion",
                r"ITEM\s+7\.?\s*MANAGEMENT['']*S?\s*DISCUSSION\s*AND\s*ANALYSIS",
                r"ITEM\s+7\.?\s*MANAGEMENT['']*S?\s*DISCUSSION",
                r"Item\s+7\.\s*Management",
                r"ITEM\s+7\.\s*MANAGEMENT",
                r"7\.\s*MANAGEMENT['']*S?\s*DISCUSSION",
                r"7\.\s*Management['']*s?\s*Discussion",
            ],
        }

        # 다음 항목 시작을 나타내는 패턴들 (더 정확하게)
        next_item_patterns = [
            r"Item\s+\d+[A-Z]?\.\s+[A-Z]",  # Item 1A. Risk 형태
            r"ITEM\s+\d+[A-Z]?\.\s+[A-Z]",  # ITEM 1A. RISK 형태
            r"Item\s+\d+[A-Z]?\s+[A-Z]",  # Item 1A Risk 형태
            r"ITEM\s+\d+[A-Z]?\s+[A-Z]",  # ITEM 1A RISK 형태
        ]

        extracted_data = {}

        # 디버깅 정보 출력
        print(f"🔍 문서 길이: {len(text_content)} characters")

        for item_name, patterns in items_to_extract.items():
            content = "해당 항목을 찾을 수 없습니다."

            # 패턴이 리스트인지 확인 (Item 8의 경우)
            if isinstance(patterns, list):
                pattern_list = patterns
            else:
                pattern_list = [patterns]

            # 모든 패턴에 대해 매치 찾기
            all_matches = []
            for pattern in pattern_list:
                matches = list(re.finditer(pattern, text_content, re.IGNORECASE))
                all_matches.extend(matches)
            print(f"\n📋 {item_name}: {len(all_matches)} 개 매치 발견")

            # 각 매치에 대해 내용 길이 확인하여 가장 긴 실제 내용 선택
            best_content = ""
            best_length = 0

            for i, match in enumerate(all_matches):
                start_index = match.end()

                # Item 7의 경우 실제 내용이 시작되는 지점을 더 정확히 찾기
                if "Management" in item_name:
                    remaining_for_search = text_content[
                        start_index : start_index + 3000
                    ]

                    # 다양한 시작 키워드들 찾기
                    start_keywords = [
                        r"\bOverview\b",
                        r"\bOVERVIEW\b",
                        r"The following.*discussion",
                        r"The following.*MD&A",
                        r"Microsoft is a",
                        r"We generate revenue",
                        r"Our industry is",
                        r"Highlights from fiscal year",
                    ]

                    for keyword_pattern in start_keywords:
                        keyword_match = re.search(
                            keyword_pattern, remaining_for_search, re.IGNORECASE
                        )
                        if keyword_match:
                            start_index += keyword_match.start()
                            print(
                                f"    Item 7: '{keyword_pattern}' 키워드로 시작점 조정: {start_index}"
                            )
                            break

                # 다음 항목의 시작 위치 찾기 (여러 패턴 시도)
                remaining_text = text_content[start_index:]
                next_match = None
                best_match_pos = len(remaining_text)

                # Item 7의 경우 특별히 Item 7A나 Item 8을 찾도록 조정
                if "Management" in item_name:
                    special_patterns = [
                        r"Item\s+7A\.\s+[A-Z]",  # Item 7A. Quantitative
                        r"Item\s+8\.\s+[A-Z]",  # Item 8. Financial
                        r"ITEM\s+7A\.\s+[A-Z]",  # ITEM 7A. QUANTITATIVE
                        r"ITEM\s+8\.\s+[A-Z]",  # ITEM 8. FINANCIAL
                    ]
                    search_patterns = special_patterns + next_item_patterns
                else:
                    search_patterns = next_item_patterns

                for pattern in search_patterns:
                    found_match = re.search(pattern, remaining_text, re.IGNORECASE)
                    if found_match and found_match.start() < best_match_pos:
                        next_match = found_match
                        best_match_pos = found_match.start()

                if next_match:
                    end_index = start_index + next_match.start()
                    item_content = text_content[start_index:end_index].strip()
                else:
                    # 다음 항목을 못 찾으면 더 많은 내용 추출
                    # Item 7의 경우 특별히 더 많은 내용 허용
                    max_length = 50000 if "Management" in item_name else 30000
                    item_content = text_content[
                        start_index : start_index + max_length
                    ].strip()

                word_count = len(item_content.split())
                print(
                    f"  매치 {i + 1}: 위치 {match.start()}-{match.end()}, 단어 수: {word_count}"
                )
                print(f"    매치 텍스트: '{match.group()}'")
                print(f"    내용 미리보기: '{item_content[:100]}...'")

                # Item 7은 더 관대한 기준 적용 (일단 긴 내용을 추출 후 후처리)
                if "Management" in item_name:
                    min_words = 20  # 일단 낮은 기준으로 추출
                    print(f"    Item 7 특별 처리 - 최소 단어 수: {min_words}")
                else:
                    min_words = 15

                # 실제 본문으로 판단되는 조건:
                print("    목차 검사 시작...")
                is_toc = self._is_table_of_contents(item_content)

                if word_count > min_words and word_count > best_length and not is_toc:
                    best_content = item_content
                    best_length = word_count
                    print(f"    ✅ 최적 내용으로 선택 (단어 수: {word_count})")
                else:
                    print("    ❌ 제외 (단어 수 부족 또는 목차)")

            if best_content:
                content = best_content

                # Item 7의 경우 특별한 후처리 - 짧은 내용이면 더 많이 추출
                if "Management" in item_name and len(content.split()) < 1000:
                    print(
                        f"    Item 7 후처리: 내용이 짧아서({len(content.split())} 단어) 더 많이 추출 시도"
                    )
                    # 매치된 위치에서 더 많은 내용 추출
                    if all_matches:
                        best_match = max(
                            all_matches,
                            key=lambda m: len(
                                text_content[m.end() : m.end() + 5000].split()
                            ),
                        )
                        extended_start = best_match.end()
                        extended_content = text_content[
                            extended_start : extended_start + 80000
                        ]  # 훨씬 더 많은 내용

                        # 다음 Item 찾기
                        for pattern in [r"Item\s+7A\.\s+", r"Item\s+8\.\s+"]:
                            next_item = re.search(
                                pattern, extended_content, re.IGNORECASE
                            )
                            if next_item:
                                extended_content = extended_content[: next_item.start()]
                                break

                        if len(extended_content.split()) > len(content.split()):
                            content = extended_content.strip()
                            print(
                                f"    Item 7 확장 성공: {len(content.split())} 단어로 증가"
                            )

                # 너무 긴 내용은 확장된 길이로 요약 (더 많은 내용 포함)
                if len(content) > 20000:
                    content = content[:20000] + "..."

            extracted_data[item_name] = (
                content if content.strip() else "내용이 없거나 추출에 실패했습니다."
            )
            print(f"📄 {item_name} 최종 결과: {len(content)} characters")

        return extracted_data

    def _is_table_of_contents(self, content: str) -> bool:
        """내용이 목차인지 판단하는 헬퍼 함수 (기준 매우 완화)"""
        content_lower = content.lower()

        # 실제 내용임을 나타내는 강력한 지표들
        business_indicators = [
            "company",
            "business",
            "operations",
            "strategy",
            "products",
            "services",
            "customers",
            "market",
            "competition",
            "technology",
            "revenue",
            "employees",
            "management",
            "discussion",
            "analysis",
            "results",
            "financial condition",
            "fiscal year",
            "growth",
            "demand",
            "supply",
            "challenges",
            "development",
        ]

        business_count = sum(
            1 for indicator in business_indicators if indicator in content_lower
        )

        # Management Discussion의 경우 기준을 더 완화
        required_indicators = (
            2 if "management" in content_lower or "discussion" in content_lower else 3
        )

        if business_count >= required_indicators:
            print(
                f"    비즈니스 내용 지표 발견으로 실제 내용 판단: {business_count} 개"
            )
            return False

        # 너무 짧은 내용만 목차로 판단 (기준 더욱 완화: 30 → 20)
        if len(content.strip()) < 20:
            print(f"    너무 짧은 내용으로 목차 의심: {len(content)} chars")
            return True

        # 점선 패턴이 매우 많이 있으면 목차 (기준 완화: 10 → 15)
        dot_pattern_count = len(re.findall(r"[.]{8,}", content))
        if dot_pattern_count > 15:
            print(f"    점선 패턴이 많아 목차로 판단: {dot_pattern_count} 개")
            return True

        # 페이지 번호 패턴이 매우 많이 있으면 목차 (기준 완화: 30 → 40)
        page_number_count = len(re.findall(r"\d{1,3}\s*$", content, re.MULTILINE))
        if page_number_count > 40:
            print(f"    페이지 번호 패턴이 많아 목차로 판단: {page_number_count} 개")
            return True

        # 목차 특징 단어들이 매우 많이 있으면 목차 (기준 완화: 5 → 8)
        toc_keywords = ["table of contents", "contents", "………"]
        keyword_count = sum(content_lower.count(keyword) for keyword in toc_keywords)
        if keyword_count > 8:
            print(f"    목차 키워드가 많아 목차로 판단: {keyword_count} 개")
            return True

        print("    실제 내용으로 판단")
        return False

    def analyze_company_report(
        self, company_identifier: str, report_type: str = "10-K"
    ) -> str:
        """회사의 SEC 보고서를 분석하여 포맷된 결과 반환"""
        try:
            # 회사 파일링 정보 가져오기
            filing_data = self.get_company_filings(company_identifier)

            if not filing_data:
                return f"❌ '{company_identifier}'에 대한 회사 정보를 찾을 수 없습니다."

            company_info = filing_data["company_info"]
            recent_filings = filing_data["recent_filings"]
            cik = filing_data["cik"]

            # 보고서 타입에 맞는 파일링 필터링
            form_types = recent_filings["form"]
            filing_dates = recent_filings["filingDate"]
            accession_numbers = recent_filings["accessionNumber"]

            target_filings = []
            for i, form in enumerate(form_types):
                if form == report_type:
                    target_filings.append(
                        {
                            "form": form,
                            "filingDate": filing_dates[i],
                            "accessionNumber": accession_numbers[i],
                        }
                    )

            if not target_filings:
                return f"❌ '{company_info['name']}'의 {report_type} 파일링을 찾을 수 없습니다."

            # 결과 포맷팅
            result = (
                f"📊 **SEC {report_type} 보고서 분석** - {company_info['name']}\n\n"
            )

            # 회사 기본 정보
            result += "### 🏢 회사 정보\n"
            result += f"• **회사명**: {company_info['name']}\n"
            result += f"• **CIK**: {company_info['cik']}\n"
            result += f"• **티커**: {', '.join(company_info.get('tickers', ['N/A']))}\n"
            result += f"• **업종**: {company_info.get('sicDescription', 'N/A')}\n\n"

            # 최신 보고서 분석
            latest_filing = target_filings[0]
            result += f"### 📄 최신 {report_type} 보고서 요약 ({latest_filing['filingDate']})\n"

            document_content = self.get_10k_document_content(
                cik, latest_filing["accessionNumber"]
            )

            if document_content:
                if report_type == "10-K":
                    extracted_items = self.extract_10k_items(document_content)
                    for item_name, content in extracted_items.items():
                        result += f"#### {item_name}\n"
                        result += f"```\n{content}\n```\n\n"
                else:  # 10-Q 또는 기타 보고서
                    # 10-Q의 경우, 간단한 미리보기 제공
                    cleaned_text = self.clean_html(document_content)
                    preview = cleaned_text[:2000].replace("\n", " ").strip()
                    result += f"**보고서 미리보기:**\n{preview}...\n\n"
            else:
                result += "보고서 내용을 가져오는 데 실패했습니다.\n\n"

            # 분석 링크 제공
            edgar_link = f"https://www.sec.gov/edgar/browse/?CIK={cik}"
            result += "### 🔗 추가 정보\n"
            result += f"• **SEC EDGAR 페이지**: {edgar_link}\n"
            result += f"• **최신 파일링 날짜**: {latest_filing['filingDate']}\n"
            result += f"• **Accession Number**: {latest_filing['accessionNumber']}\n"

            return result

        except Exception as e:
            return f"❌ SEC 보고서 분석 중 오류 발생: {str(e)}"
