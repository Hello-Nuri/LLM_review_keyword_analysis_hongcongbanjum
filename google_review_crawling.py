from playwright.sync_api import sync_playwright
import time
import csv

# 특정 URL로 직접 이동
def go_to_url(page, url):
    page.goto(url)
    time.sleep(3)  # 페이지 로딩을 기다리기 위해 잠시 대기

# 리뷰 탭 클릭
def click_reviews_tab(page):
    reviews_tab_selector = "button[aria-label*='리뷰']"
    reviews_tab_button = page.query_selector(reviews_tab_selector)
    if reviews_tab_button:
        reviews_tab_button.click()
        time.sleep(3)  # 리뷰 탭 로딩을 기다리기 위해 잠시 대기

# 리뷰를 하나씩 스크롤하며 '자세히' 버튼을 클릭하고 크롤링
def crawl_reviews(page):
    reviews = []
    while True:
        review_elements = page.query_selector_all("div.jftiEf")
        for review_element in review_elements:
            # '자세히' 버튼 클릭 시도
            try:
                show_more_button = review_element.query_selector("div.MyEned button")
                if show_more_button and show_more_button.inner_text() == "자세히":
                    show_more_button.click()
                    time.sleep(1)
            except Exception as e:
                print(f"Failed to click '자세히' button: {e}")

            # 리뷰 데이터 수집
            rating_tag = review_element.query_selector("span.kvMYJc")
            review_text_tag = review_element.query_selector("div.MyEned")
            rating = rating_tag.get_attribute("aria-label") if rating_tag else "No rating"
            review_text = review_text_tag.inner_text() if review_text_tag else "No text"
            reviews.append({
                "rating": rating,
                "review_text": review_text
            })

        # 특정 위치로 이동
        try:
            scroll_target = page.query_selector("div.lXJj5c.Hk4XGb > div.qjESne")
            if scroll_target:
                scroll_target.scroll_into_view_if_needed()
                time.sleep(2)
            else:
                break
        except Exception as e:
            print(f"Failed to scroll: {e}")
            break

    return reviews

# 수집된 리뷰 데이터를 CSV 파일로 저장
def write_data(store_name, data):
    file_name = f"./data/reviews_{store_name}.csv"
    with open(file_name, "w", encoding="utf-8-sig", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=["rating", "review_text"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == '__main__':
    csv_file = "hongkong_re_crawling_url.csv"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        page = browser.new_page()

        with open(csv_file, "r", encoding="ansi") as file:
            reader = csv.DictReader(file)
            for row in reader:
                store_name = row["store_name"]
                review_url = row["review_url"]
                print(f"Processing {store_name}...")

                # 특정 URL로 이동
                go_to_url(page, review_url)
                time.sleep(3)

                # 리뷰 탭 클릭
                click_reviews_tab(page)

                # 리뷰 크롤링
                reviews_data = crawl_reviews(page)

                # 데이터 저장
                write_data(store_name, reviews_data)

        browser.close()
