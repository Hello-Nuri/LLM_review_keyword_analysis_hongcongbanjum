from playwright.sync_api import sync_playwright
import time
import csv
import os

# 특정 URL로 직접 이동
def go_to_url(page, url):
    page.goto(url)
    time.sleep(5)  # 페이지 로딩을 기다리기 위해 대기 시간 증가

# 댓글 섹션으로 이동 (최초 및 크롤링 중 모두 사용)
def scroll_to_continuations(page):
    try:
        continuation_section = page.wait_for_selector("div#continuations.style-scope.ytd-item-section-renderer", timeout=120000)
        if continuation_section:
            continuation_section.scroll_into_view_if_needed()
            time.sleep(5)  # 스크롤 후 대기 시간 증가
        else:
            print("Continuation section not found or all comments loaded.")
    except:
        print("Continuation section took too long to load.")

# 댓글을 크롤링
def crawl_comments(page, existing_comments_count):
    comments = []
    new_comments_count = 0

    # 댓글 영역 설정
    comment_section = page.query_selector("ytd-comments#comments.style-scope.ytd-watch-flexy")
    if not comment_section:
        print("Comment section not found.")
        return comments

    # 댓글 목록 크롤링
    comment_elements = comment_section.query_selector_all("ytd-comment-thread-renderer")
    for comment_element in comment_elements[existing_comments_count:]:
        text_tag = comment_element.query_selector("span.yt-core-attributed-string[role='text']")
        like_tag = comment_element.query_selector("span#vote-count-middle")
        text = text_tag.inner_text() if text_tag else "No text"
        likes = like_tag.inner_text().strip() if like_tag else "0"
        comments.append({
            "comment_text": text,
            "likes": likes
        })
        new_comments_count += 1

        if new_comments_count >= 500:
            return comments

    # 추가 댓글 로드 시 이동
    scroll_to_continuations(page)

    return comments

# 수집된 댓글 데이터를 CSV 파일로 저장
def write_data(data, file_index):
    if not os.path.exists("./data_youtube"):
        os.makedirs("./data_youtube")

    file_name = f"./data_youtube/youtube_{file_index}.csv"
    with open(file_name, "w", encoding="utf-8-sig", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=["comment_text", "likes"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == '__main__':
    start_url = "https://www.youtube.com/watch?v=mSACOKgkc3U"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        page = browser.new_page()

        # 특정 URL로 이동
        go_to_url(page, start_url)
        time.sleep(5)  # 대기 시간 증가

        # 댓글 섹션으로 이동 (최초)
        scroll_to_continuations(page)

        all_comments = []
        file_index = 500

        while True:
            # 댓글 크롤링
            new_comments = crawl_comments(page, len(all_comments))
            if not new_comments:
                break

            all_comments.extend(new_comments)

            # 500개씩 파일로 저장
            if len(all_comments) >= file_index:
                write_data(all_comments[:file_index], file_index)
                all_comments = all_comments[file_index:]
                file_index += 500

            # 추가 댓글 로드 시 이동 (크롤링 중)
            scroll_to_continuations(page)

        # 남은 댓글 저장
        if all_comments:
            write_data(all_comments, file_index)

        browser.close()
