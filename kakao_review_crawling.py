
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time

def parse_store_info(soup):
    """BeautifulSoup 객체를 사용하여 리뷰 정보 추출"""
    store_name = soup.find('h3', class_='tit_location').text.strip() \
        if soup.find('h3', class_='tit_location') else None

    reviews = []
    review_elements = soup.find_all('div', class_='inner_grade')

    for review in review_elements:
        user_star = review.find('span', class_='ico_star inner_star')['style'].replace('width:', '').replace('%',
                                                                                                             '').strip() \
            if review.find('span', class_='ico_star inner_star') else None

        review_content = review.find('p', class_='txt_comment').text.strip() \
            if review.find('p', class_='txt_comment') else None

        review_date = review.find('span', class_='time_write').text.strip() \
            if review.find('span', class_='time_write') else None

        reviews.append({
            'store_name': store_name,
            'user_star': user_star,
            'review_content': review_content,
            'review_date': review_date
        })

    return reviews

def close_modal(page):
    """플로팅 배너를 닫기"""
    try:
        # 플로팅 배너 닫기 버튼 클릭
        close_button_selector = "div.floating_bnr div.inner_floating a.btn_close"
        close_button = page.query_selector(close_button_selector)
        if close_button:
            close_button.click()
            print("플로팅 배너를 닫았습니다.")
            # 모달이 닫힐 때까지 대기
            page.wait_for_selector(close_button_selector, state='hidden', timeout=10000)
            time.sleep(2)  # 모달 닫고 페이지 안정화 대기
        else:
            print("플로팅 배너 닫기 버튼을 찾을 수 없습니다.")
    except Exception as e:
        print(f"모달 닫기 중 오류 발생: {str(e)}")

def scrape_page(page):
    """페이지에서 '후기 더보기' 버튼을 클릭하여 모든 리뷰 로드"""
    close_modal(page)  # 페이지 로딩 후 모달 닫기

    while True:
        try:
            # "후기 더보기" 버튼이 있는지 확인
            more_buttons = page.query_selector_all("a.link_more")
            more_button = None

            for button in more_buttons:
                if button.is_visible() and "후기 더보기" in button.inner_text():
                    more_button = button
                    break

            if more_button:
                # 버튼이 보이도록 스크롤
                more_button.scroll_into_view_if_needed()
                # 클릭
                more_button.click(timeout=60000)
                # 클릭 후 로딩 대기
                page.wait_for_load_state('networkidle')  # 네트워크가 안정될 때까지 대기
                time.sleep(3)  # 페이지 로딩 대기
            else:
                print("더 이상의 '후기 더보기' 버튼이 없습니다.")
                break
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            break

def crawl_review_page_html(url):
    """웹 페이지를 로드하고 리뷰를 모두 크롤링"""
    with sync_playwright() as p:
    # 브라우저를 열고 페이지 생성
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url)
        time.sleep(5)  # 페이지 로딩 대기
        scrape_page(page)
        html = page.content()
        browser.close()
    return html

def save_reviews_to_csv(reviews, file_name):
    """리뷰 데이터를 CSV 파일로 저장"""
    df = pd.DataFrame(reviews)
    df.to_csv(file_name, index=False, encoding='utf-8-sig')
    print(f"리뷰 데이터를 '{file_name}'에 저장했습니다.")

# if __name__ == '__main__':
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)  # headless=True로 설정하면 브라우저 UI가 보이지 않음
#         page = browser.new_page()
#         url = "https://place.map.kakao.com/m/336646124#comment"  # 크롤링할 URL
#         html = crawl_review_page_html(page, url)
#         soup = BeautifulSoup(html, 'lxml')
#         reviews = parse_store_info(soup)
#         print(f"총 리뷰 수: {len(reviews)}")
#
#         # 리뷰 데이터를 CSV 파일로 저장
#         save_reviews_to_csv(reviews, "reviews.csv")
#
#         browser.close()

if __name__ == '__main__':
    # CSV 파일에서 URL 리스트를 불러오기
    input_csv_file = "/Users/nuri.park/Desktop/multicampus/data_analytics_camp_9th/Nuri_project_folder/semi_project_2_0808/kakaomap_review_crawling/data/seoul_kakaomap_url_list.csv"  # URL이 포함된 CSV 파일 경로
    urls_df = pd.read_csv(input_csv_file)

    all_reviews = []

        # 각 URL에 대해 크롤링 수행
    for index, row in urls_df.iterrows():
        url = row['URL_kakao']
        print(f"크롤링할 URL: {url}")

        html = crawl_review_page_html(url)
        soup = BeautifulSoup(html, 'lxml')
        reviews = parse_store_info(soup)
        all_reviews.extend(reviews)  # 모든 리뷰를 하나의 리스트에 추가

    # 모든 리뷰 데이터를 CSV 파일로 저장
    save_reviews_to_csv(all_reviews, "all_reviews.csv")











