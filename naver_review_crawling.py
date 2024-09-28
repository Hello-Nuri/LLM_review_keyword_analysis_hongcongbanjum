from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import csv


def read_data():
    store_info = []
    with open("/Users/nuri.park/Desktop/multicampus/data_analytics_camp_9th/Nuri_project_folder/semi_project_2_0808/seoul_hongkong0410.csv", "r", encoding="utf-8") as fr:
        reader = csv.DictReader(fr)
        for row in reader:
            store_name = row["브랜드"] + " " + row["매장명"]
            store_url = row["URL"]
            store_info.append([store_name, store_url])
    return store_info

def load_all_reviews(playwright_page):
    while True:
        try:
            # "리뷰가 더 있습니다" 버튼이 있는지 확인하고 클릭
            additional_button = playwright_page.query_selector("a[role='button'][data-pui-click-code='keywordmore']")
            if additional_button and additional_button.is_enabled():
                additional_button.click(timeout=240000)
                time.sleep(1)  # 클릭 후 로딩 대기
                continue

            # "더보기" 버튼이 있는지 확인하고 클릭
            more_button = playwright_page.query_selector("a.fvwqf")
            if more_button and more_button.is_enabled():
                more_button.click(timeout=240000)
                time.sleep(1)  # 클릭 후 로딩 대기
                continue

            # 더 이상 클릭할 버튼이 없으면 종료
            print("더 이상의 더보기 버튼이 없습니다.")
            break
        except Exception as e:
            print(f"‘리뷰가 더 있습니다’ 버튼 클릭 중 오류 발생: {str(e)}")
            break  # 오류 발생 시 루프 종료


def crawl_review_page_html(playwright_page, url):
    playwright_page.goto(url)
    time.sleep(5)
    load_all_reviews(playwright_page)
    html = playwright_page.content()
    return html


def parse_review_page(html, store_name):
    soup = BeautifulSoup(html, "lxml")

    review_items = soup.find_all("li", class_="pui__X35jYm EjjAW")
    data = []

    for item in review_items:
        review_text_element = item.find("div", class_="pui__vn15t2")
        if review_text_element:
            for br in review_text_element.find_all("br"):
                br.replace_with(" ")

            review_text = review_text_element.get_text(separator=" ", strip=True)
        else:
            review_text = "No review text"

        # "음식이 맛있어요" 부분
        additional_info = item.find("div", class_="pui__HLNvmI")
        if additional_info:
            # 모든 <span> 태그에서 텍스트 추출
            additional_text_elements = additional_info.find_all("span", class_="pui__jhpEyP")
            additional_texts = [element.get_text(strip=True) for element in additional_text_elements]
            additional_text = ", ".join(additional_texts)
        else:
            additional_text = "추가 정보 없음"

        # 날짜 부분
        review_date_div = item.find("div", class_="pui__QKE5Pr")
        if review_date_div:
            time_element = review_date_div.find("time", attrs={"aria-hidden": "true"})
            review_date = time_element.get_text(strip=True) if time_element else "No review date"
        else:
            review_date = "No review date div"

        data.append({
            "store_name": store_name,
            "review_text": review_text,
            "additional_info": additional_text,
            "review_date": review_date
        })
    return data

def write_data(data, number):
    file_name = f"/Users/nuri.park/Desktop/multicampus/data_analytics_camp_9th/Nuri_project_folder/semi_project_2_0808/review_crawling_{number}.csv"
    with open(file_name, "w", encoding="utf-8", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=["store_name", "review_text", "additional_info", "review_date"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == '__main__':
    store_info = read_data()
    target_stores = [
        "홍콩반점0410 신대방삼거리역점"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        playwright_page = browser.new_page()

        for store_name, url in store_info:
            if store_name in target_stores:
                print(f"{store_name} 지점의 리뷰 수집 시작.")
                html = crawl_review_page_html(playwright_page, url)
                review_data = parse_review_page(html, store_name)
                print(f"{store_name} 지점의 리뷰 {len(review_data)}개 수집 완료.")
                write_data(review_data, store_info.index([store_name, url]) + 1)

        browser.close()