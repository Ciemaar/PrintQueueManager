from hypothesis import given, strategies as st
from pydantic import ValidationError
from src.worker.llm_scraper import ExtractedModelInfo, ScrapedPageData

@given(st.text(), st.from_regex(r"^https?://[a-zA-Z0-9.-]+(?:/[a-zA-Z0-9.-]*)*$"), st.one_of(st.none(), st.from_regex(r"^https?://[a-zA-Z0-9.-]+(?:/[a-zA-Z0-9.-]*)*$")), st.one_of(st.none(), st.text()))
def test_extracted_model_info_valid(title: str, url: str, thumbnail: str | None, author: str | None) -> None:
    # Hypothesis test to ensure our Pydantic schema handles varying types of data well
    try:
        model = ExtractedModelInfo(title=title, url=url, thumbnail=thumbnail, author=author)
        assert model.title == title
        assert model.url == url
        assert model.thumbnail == thumbnail
        assert model.author == author
    except ValidationError:
        pass

def test_scraped_page_data_valid() -> None:
    model1 = ExtractedModelInfo(title="A", url="http://a.com", thumbnail=None, author="Bob")
    page = ScrapedPageData(models=[model1])
    assert len(page.models) == 1
    assert page.models[0].title == "A"
