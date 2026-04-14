with open("src/app/main.py", "r") as f:
    c = f.read()

c = c.replace('import os\n            # We inject the credential into environment temporarily for test to avoid refactoring get_page_html now\n            # Or better, we patch the get_page_html to take credential\n            os.environ[f"{service_name.upper()}_TEST_CRED"] = credential\n            fetched_html = get_page_html(service_name, target_url)', 'fetched_html = get_page_html(service_name, target_url, credential)')

with open("src/app/main.py", "w") as f:
    f.write(c)

with open("src/worker/llm_scraper.py", "r") as f:
    c = f.read()

# We need to make run_scraper accept credential too
c = c.replace('def run_scraper(source: str, url: str) -> List[dict[str, Any]]:', 'def run_scraper(source: str, url: str, credential: str = "") -> List[dict[str, Any]]:')
c = c.replace('html_content = get_page_html(source, url)', 'html_content = get_page_html(source, url, credential)')
with open("src/worker/llm_scraper.py", "w") as f:
    f.write(c)
