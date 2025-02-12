import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.extractor import get_extractor, extract_text_from_pdf
import pytest

test_cases = [
    # Source, Para
    ("tests/data/test1.pdf", {'extract_img': False}, "##Headerfirstlineภาษาไทยสวัสดีครับ|1|2|3||-----|-------|-----------||ไฟล์|นี|มี||ไว้|สําหรับ|ทดสอบ||..|Hello|TestCase|")
]


@pytest.mark.parametrize("source,params,expected", test_cases)
def test_valid_extraction(source, params, expected):
    """
    Test if the extractor can extract at least text on the pdf file.
    """
    extractor = get_extractor()
    results = extract_text_from_pdf(source, extractor=extractor, **params)

    # Post process
    results = results.strip().replace("\n", "").replace(" ", "")

    assert results == expected
