import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime


def crawl_job_posts(keyword, pages=1):
    """
    사람인 채용공고를 크롤링하는 함수
    """

    jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for page in range(1, pages + 1):
        url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword={keyword}&recruitPage={page}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 채용공고 목록 가져오기
            job_listings = soup.select('.item_recruit')

            for job in job_listings:
                try:
                    # 회사명 - 수정된 부분
                    company = job.select_one('.corp_name a').text.strip()

                    # 회사 정보 링크
                    company_info = 'https://www.saramin.co.kr' + job.select_one('.corp_name a')['href']

                    # 채용 제목
                    title = job.select_one('.job_tit a').text.strip()

                    # 채용 링크
                    post_link = 'https://www.saramin.co.kr' + job.select_one('.job_tit a')['href']

                    # 지역, 경력, 학력, 고용형태, 연봉정보
                    conditions = job.select('.job_condition span')
                    location = conditions[0].text.strip() if len(conditions) > 0 else ''
                    career_level = conditions[1].text.strip() if len(conditions) > 1 else ''
                    education = conditions[2].text.strip() if len(conditions) > 2 else ''
                    employment_type = conditions[3].text.strip() if len(conditions) > 3 else ''
                    salary_range = conditions[4].text.strip() if len(conditions) > 4 else ''

                    # 마감일
                    deadline = job.select_one('.job_date .date').text.strip()

                    # 직무 분야
                    job_sectors = job.select_one('.job_sector')
                    sector_text = job_sectors.text.strip() if job_sectors else ''

                    if '수정일' in sector_text:
                        job_sector = sector_text.split('수정일')[0].strip()
                        posted_date = sector_text.split('수정일')[1].strip()
                    elif '등록일' in sector_text:
                        job_sector = sector_text.split('등록일')[0].strip()
                        posted_date = sector_text.split('등록일')[1].strip()
                    else:
                        job_sector = sector_text
                        posted_date = ''

                    # 기술 리스트로 분리
                    if job_sector:
                        job_sector = [skill.strip(',').strip() for skill in job_sector.split()]
                    else:
                        job_sector = []


                    # posted_date에서 날짜 부분만 추출 (예: "24/11/25")
                    if posted_date:
                        posted_date = posted_date[-8:].strip()

                    # 트렌드 키워드 정보 (있는 경우)
                    trend_badge = job.select_one('.area_badge .badge')
                    trend_keywords = trend_badge.text.strip() if trend_badge else ''

                    # 마감일 & 상태 처리
                    today = datetime.today().date()

                    if deadline:
                        # '~ 12/27(금)' -> '12/27'
                        deadline = deadline.split(' ')[-1].split('(')[0].strip()
                        try:
                            # '12/27' -> '12/27/2024'
                            deadline = datetime.strptime(deadline, "%m/%d").replace(year=today.year).date()
                        except ValueError:
                            deadline = None
                    else:
                        deadline = None

                    # 상태 처리: 마감일이 지나지 않았으면 open, 지났으면 closed
                    status = 'closed' if deadline and deadline < today else 'open'

                    jobs.append({
                        '회사명': company,
                        '트렌드_키워드': trend_keywords,
                        '제목': title,
                        '공고 링크': post_link,
                        '지역': location,
                        '경력': career_level,
                        '학력': education,
                        '고용형태': employment_type,
                        '마감일': deadline,
                        '연봉정보': salary_range,
                        '작성날짜': datetime.strptime(posted_date, "%y/%m/%d").strftime("%Y-%m-%d"),
                        '상태': status,
                        '직무분야': job_sector,
                        '회사 정보': company_info
                    })

                except AttributeError as e:
                    print(f"항목 파싱 중 에러 발생: {e}")
                    continue

            print(f"{page}페이지 크롤링 완료")
            time.sleep(1)  # 서버 부하 방지를 위한 딜레이

        except requests.RequestException as e:
            print(f"페이지 요청 중 에러 발생: {e}")
            continue

    # return pd.DataFrame(jobs)
    return jobs

# # 사용 예시
# if __name__ == "__main__":
#     # 'python' 키워드로 3페이지 크롤링
#     df = crawl_job_posts('python', pages=1)
#     print(df)
#     df.to_csv('saramin_python.csv', index=False)