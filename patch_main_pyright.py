with open("src/app/main.py", "r") as f:
    c = f.read()

c = c.replace('fetched_html = get_page_html(service_name, target_url, credential)', 'import os\n            # We inject the credential into environment temporarily for test to avoid refactoring get_page_html now\n            # Or better, we patch the get_page_html to take credential\n            os.environ[f"{service_name.upper()}_TEST_CRED"] = credential\n            fetched_html = get_page_html(service_name, target_url)')
with open("src/app/main.py", "w") as f:
    f.write(c)

with open("src/worker/llm_scraper.py", "r") as f:
    c = f.read()

c = c.replace('def get_page_html(source: str, url: str) -> str:', 'def get_page_html(source: str, url: str, credential: str = "") -> str:')
c = c.replace('cookie_str = settings.makerworld_cookie', 'cookie_str = credential or settings.makerworld_cookie')
c = c.replace('cookie_str = settings.printables_cookie', 'cookie_str = credential or settings.printables_cookie')
c = c.replace('cookie_str = settings.cults3d_cookie', 'cookie_str = credential or settings.cults3d_cookie')
c = c.replace('cookie_str = settings.minihoarder_cookie', 'cookie_str = credential or settings.minihoarder_cookie')

with open("src/worker/llm_scraper.py", "w") as f:
    f.write(c)
