# get_page_advanced_data_to_file.py (파일 이름 통일)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from bs4.element import Comment # HTML 주석 추출을 위해 필요
import time
import os
import requests # 웹 서버 응답 시간을 측정하기 위해 requests 라이브러리 추가
import json # JSON 데이터를 깔끔하게 출력하기 위해 추가

def get_chrome_driver(headless=True):
    """
    Chrome WebDriver를 설정하고 반환합니다.
    headless=True로 설정하면 브라우저 창이 보이지 않습니다.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=options)

def extract_and_save_advanced_page_data(url, output_filename="DLRJ.txt", headless=False, wait_time=15):
    """
    지정된 URL의 웹 페이지에서 HTML 소스, 주요 요소들,
    그리고 추가적인 기술 정보들을 추출하여 파일에 저장합니다.
    """
    driver = None
    exception_occurred = False # 예외 발생 여부를 추적하는 플래그

    output_buffer = []
    output_buffer.append("=" * 70)
    output_buffer.append(f"✨ 웹 페이지 고급 데이터 추출 결과 - URL: {url} ✨")
    output_buffer.append("=" * 70)

    try:
        # --- 1. 웹 서버 응답 시간 (핑과 유사한 개념) ---
        try:
            response = requests.get(url, timeout=10) # 10초 타임아웃
            server_response_time = round(response.elapsed.total_seconds() * 1000, 2) # 밀리초 단위
            http_status_code = response.status_code
            output_buffer.append(f"\n--- 🌐 웹 서버 응답 및 상태 ---")
            output_buffer.append(f"HTTP 상태 코드: {http_status_code}")
            output_buffer.append(f"서버 응답 시간 (Requests): {server_response_time} ms\n")
        except requests.exceptions.Timeout:
            output_buffer.append("\n--- 🌐 웹 서버 응답 및 상태 ---")
            output_buffer.append("서버 응답 시간 측정 실패: 요청 시간 초과 (Timeout)")
        except requests.exceptions.RequestException as e:
            output_buffer.append("\n--- 🌐 웹 서버 응답 및 상태 ---")
            output_buffer.append(f"서버 응답 시간 측정 실패: 요청 오류 - {e}")
        output_buffer.append("\n")

        # --- Selenium을 통한 페이지 접속 및 기본 정보 추출 ---
        print(f"웹 드라이버를 시작하고 '{url}' 페이지에 접속합니다. (헤드리스 모드: {headless})")
        driver = get_chrome_driver(headless=headless)
        start_time_selenium_load = time.time() # Selenium 로딩 시작 시간 기록
        driver.get(url)

        print(f"페이지 로딩을 최대 {wait_time}초 기다리는 중...")
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        end_time_selenium_load = time.time() # Selenium 로딩 완료 시간 기록
        selenium_load_duration = round((end_time_selenium_load - start_time_selenium_load), 2)
        print(f"페이지 로딩 완료 (Selenium 소요 시간: {selenium_load_duration}초).")

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        output_buffer.append("\n--- ⏱️ 페이지 로딩 지표 (Selenium 기준) ---")
        output_buffer.append(f"Selenium 페이지 로딩 시간: {selenium_load_duration} 초\n")

        # --- 기본 정보 추출 ---
        title = soup.title.text.strip() if soup.title else "제목 없음"
        output_buffer.append(f"\n--- 📌 페이지 제목 ---\n{title}\n")

        meta_description = soup.find('meta', attrs={'name': 'description'})
        description_content = meta_description['content'].strip() if meta_description and 'content' in meta_description.attrs else "설명 없음"
        output_buffer.append(f"--- 📝 메타 설명 ---\n{description_content}\n")

        output_buffer.append("--- 📄 주요 섹션 제목 (H1, H2, H3) ---")
        headings = soup.find_all(['h1', 'h2', 'h3'])
        if headings:
            for heading in headings:
                output_buffer.append(f"<{heading.name.upper()}>: {heading.get_text(strip=True)}")
        else:
            output_buffer.append("주요 제목 태그를 찾을 수 없습니다.")
        output_buffer.append("\n")

        output_buffer.append("--- 📑 주요 텍스트 단락 (상위 5개) ---")
        paragraphs = soup.find_all('p')
        if paragraphs:
            for i, p in enumerate(paragraphs[:5]):
                text_content = p.get_text(strip=True)
                if text_content:
                    output_buffer.append(f"단락 {i+1}: {text_content[:200]}...")
            if len(paragraphs) > 5:
                output_buffer.append(f"...외 {len(paragraphs) - 5}개의 단락 더 존재합니다.")
        else:
            output_buffer.append("단락을 찾을 수 없습니다.")
        output_buffer.append("\n")

        output_buffer.append("--- 🗒️ 목록 (UL/OL) ---")
        lists = soup.find_all(['ul', 'ol'])
        if lists:
            for list_tag in lists:
                list_type = "순서 없는 목록" if list_tag.name == 'ul' else "순서 있는 목록"
                output_buffer.append(f"{list_type}:")
                list_items = list_tag.find_all('li')
                for item in list_items[:5]:
                    item_text = item.get_text(strip=True)
                    if item_text:
                        output_buffer.append(f"  - {item_text}")
                if len(list_items) > 5:
                    output_buffer.append(f"  ...외 {len(list_items) - 5}개의 항목 더.")
        else:
            output_buffer.append("목록을 찾을 수 없습니다.")
        output_buffer.append("\n")

        output_buffer.append("--- 🔗 페이지 내 모든 링크 (상위 10개) ---")
        links = soup.find_all('a', href=True)
        if links:
            for i, link in enumerate(links[:10]):
                link_text = link.get_text(strip=True)
                link_url = link['href']
                if link_text:
                    output_buffer.append(f"링크 {i+1}: 텍스트: '{link_text}', URL: '{link_url}'")
                else:
                    output_buffer.append(f"링크 {i+1}: URL: '{link_url}' (텍스트 없음)")
            if len(links) > 10:
                output_buffer.append(f"...외 {len(links) - 10}개의 링크 더 존재합니다.")
        else:
            output_buffer.append("링크를 찾을 수 없습니다.")
        output_buffer.append("\n")

        output_buffer.append("--- 🖼️ 페이지 내 모든 이미지 (상위 5개) ---")
        images = soup.find_all('img', src=True)
        if images:
            for i, img in enumerate(images[:5]):
                img_src = img['src']
                img_alt = img.get('alt', '대체 텍스트 없음')
                output_buffer.append(f"이미지 {i+1}: SRC: '{img_src}', ALT: '{img_alt}'")
            if len(images) > 5:
                output_buffer.append(f"...외 {len(images) - 5}개의 이미지가 더 존재합니다.")
        else:
            output_buffer.append("이미지를 찾을 수 없습니다.")
        output_buffer.append("\n")

        # --- 추가 정보 추출 ---

        # 8. HTML 주석
        output_buffer.append("--- 💬 HTML 주석 ---")
        # BS4 Comment 객체를 직접 임포트하여 사용
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        if comments:
            for i, comment in enumerate(comments[:5]):
                output_buffer.append(f"주석 {i+1}: {comment.strip()[:100]}...")
            if len(comments) > 5:
                output_buffer.append(f"...외 {len(comments) - 5}개의 주석 더 존재합니다.")
        else:
            output_buffer.append("HTML 주석을 찾을 수 없습니다.")
        output_buffer.append("\n")

        # 9. 폼 (Form) 정보
        output_buffer.append("--- 📝 폼 (Form) 정보 ---")
        forms = soup.find_all('form')
        if forms:
            for i, form in enumerate(forms):
                output_buffer.append(f"폼 {i+1}:")
                output_buffer.append(f"  액션 (action): {form.get('action', '없음')}")
                output_buffer.append(f"  메서드 (method): {form.get('method', '없음')}")
                input_fields = form.find_all(['input', 'textarea', 'select'])
                if input_fields:
                    output_buffer.append("  입력 필드:")
                    for field in input_fields[:5]:
                        field_name = field.get('name', '이름 없음')
                        field_type = field.get('type', field.name)
                        output_buffer.append(f"    - 타입: {field_type}, 이름: {field_name}")
                    if len(input_fields) > 5:
                        output_buffer.append(f"    ...외 {len(input_fields) - 5}개의 필드 더.")
                else:
                    output_buffer.append("  입력 필드를 찾을 수 없습니다.")
        else:
            output_buffer.append("폼을 찾을 수 없습니다.")
        output_buffer.append("\n")

        # 10. 스크립트 파일 및 스타일시트 링크
        output_buffer.append("--- ⚙️ 외부 리소스 (JS/CSS) ---")
        scripts = soup.find_all('script', src=True)
        styles = soup.find_all('link', rel='stylesheet', href=True)
        if scripts:
            output_buffer.append("스크립트 파일:")
            for i, script in enumerate(scripts[:5]):
                output_buffer.append(f"  {i+1}: {script['src']}")
            if len(scripts) > 5:
                output_buffer.append(f"  ...외 {len(scripts) - 5}개의 스크립트 더.")
        if styles:
            output_buffer.append("스타일시트 파일:")
            for i, style in enumerate(styles[:5]):
                output_buffer.append(f"  {i+1}: {style['href']}")
            if len(styles) > 5:
                output_buffer.append(f"  ...외 {len(styles) - 5}개의 스타일시트 더.")
        if not scripts and not styles:
            output_buffer.append("외부 스크립트 및 스타일시트 파일을 찾을 수 없습니다.")
        output_buffer.append("\n")

        # 11. 특정 메타 태그 (Charset, Viewport 등)
        output_buffer.append("--- 🛠️ 기타 메타 태그 ---")
        meta_tags = soup.find_all('meta')
        useful_meta_tags = ['charset', 'viewport', 'keywords', 'author', 'generator', 'application-name']
        found_meta = False
        for meta in meta_tags:
            name = meta.get('name')
            http_equiv = meta.get('http-equiv')
            if name in useful_meta_tags or http_equiv:
                content = meta.get('content', '')
                if name:
                    output_buffer.append(f"  {name}: {content}")
                elif http_equiv:
                    output_buffer.append(f"  {http_equiv}: {content}")
                found_meta = True
            elif 'charset' in meta.attrs:
                output_buffer.append(f"  charset: {meta.get('charset', '없음')}")
                found_meta = True

        if not found_meta:
            output_buffer.append("특정 메타 태그를 찾을 수 없습니다.")
        output_buffer.append("\n")

        # 12. 현재 페이지의 모든 쿠키 정보 (세션 관리 등 확인)
        output_buffer.append("--- 🍪 쿠키 정보 ---")
        cookies = driver.get_cookies()
        if cookies:
            output_buffer.append(json.dumps(cookies, indent=2, ensure_ascii=False))
        else:
            output_buffer.append("쿠키 정보를 찾을 수 없습니다.")
        output_buffer.append("\n")


        output_buffer.append("=" * 70)
        output_buffer.append("--- 📄 원본 HTML 소스 ---")
        output_buffer.append("=" * 70)
        output_buffer.append(html)

        # --- 파일에 저장 ---
        full_path = os.path.join(os.getcwd(), output_filename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_buffer))

        print(f"\n✅ 데이터 추출 및 '{output_filename}' 파일 저장 완료!")
        print(f"파일 경로: {full_path}")

    except TimeoutException as e: # 예외 객체 e를 명시적으로 catch
        exception_occurred = True
        print("\n--- 🚨 오류 발생 🚨 ---")
        print(f"페이지 로딩 시간이 초과되었습니다 ({wait_time}초). 네트워크 연결을 확인하거나, 'wait_time'을 늘려보세요.")
        print(f"오류 상세: {e}")
        print("브라우저를 닫지 않고 유지합니다.")
    except WebDriverException as e: # 예외 객체 e를 명시적으로 catch
        exception_occurred = True
        print("\n--- 🚨 오류 발생 🚨 ---")
        print(f"WebDriver 오류가 발생했습니다: {e}")
        print("Chrome 브라우저와 ChromeDriver의 버전이 일치하는지 확인해주세요.")
        print("브라우저를 닫지 않고 유지합니다.")
    except Exception as e: # 예외 객체 e를 명시적으로 catch
        exception_occurred = True
        print("\n--- 🚨 예상치 못한 오류 발생 🚨 ---")
        print(f"오류 내용: {e}")
        print("예상치 못한 문제가 발생했습니다. 코드 논리나 환경 설정을 확인해주세요.")
    finally:
        # exception_occurred 플래그를 사용하여 driver.quit() 호출 여부 결정
        if driver and not exception_occurred:
            print("웹 드라이버를 종료합니다.")
            driver.quit()
        elif driver and exception_occurred:
            print("오류 발생으로 인해 브라우저를 닫지 않고 유지합니다.")


if __name__ == "__main__":
    # 크롤링할 웹사이트 URL 설정
    target_url = "https://gbsm.newrrow.com/csr-platform/home"

    # 함수 호출하여 데이터 추출 및 파일에 저장
    # headless=False로 설정하면 브라우저 창이 실제로 열려서 과정을 볼 수 있습니다.
    # 디버깅이 필요 없다면 headless=True로 변경하세요.
    extract_and_save_advanced_page_data(target_url, output_filename="DLRJ.txt", headless=False, wait_time=20)