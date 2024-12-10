import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def crawl_company_info(company_name, link):
    """
    사람인 회사 정보를 크롤링하는 함수
    """

    company_info = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    url = f"{link}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 회사 정보 가져오기
        company_infos = soup.select('.area_company_infos')

        for company in company_infos:
            try:
                # 기업 형태
                company_summary_tit = company.select('.company_summary_tit')
                if len(company_summary_tit) > 1:  # [1]이 있는지 확인
                    company_type = company_summary_tit[1].text.strip()
                    if company_type.endswith("명"):
                        company_type = None
                else:
                    company_type = None

                # 업종
                industry = soup.find('dt', string='업종')
                industry = industry.find_next('dd').get_text(strip=True) if industry else '정보 없음'

                # 홈페이지
                website = soup.find('dt', string='홈페이지')
                website = website.find_next('dd').find('a')['href'] if website else '정보 없음'

                # 주소
                address = soup.find('dt', string='주소')
                address = address.find_next('dd').find('p', class_='ellipsis').get_text(strip=True) if address else '정보 없음'

                # 기업 설명
                introduce = company.select_one('.company_introduce').text.strip() if company.select_one('.company_introduce') else '정보 없음'

                company_info.append({
                    '회사명': company_name,
                    '기업 형태': company_type,
                    '업종': industry,
                    '홈페이지': website,
                    '주소': address,
                    '기업 설명': introduce,
                })

            except AttributeError as e:
                print(f"항목 파싱 중 에러 발생: {e}")
                continue

        print(f"{company_name} 정보 크롤링 완료")
        time.sleep(1)  # 서버 부하 방지를 위한 딜레이

    except requests.RequestException as e:
        print(f"페이지 요청 중 에러 발생: {e}")

    # return pd.DataFrame(company_info)
    return company_info

# # 사용 예시
# if __name__ == "__main__":
#     df = crawl_company_info('(주)이노플러스컴퍼니','https://www.saramin.co.kr/zf_user/company-info/view?csn=RERNRGFMdytKOTBycyt4U1dnMUwyUT09')
#     print(df)
#     df.to_csv('saramin_company.csv', index=False)