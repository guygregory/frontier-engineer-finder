"""Playwright tests for the Frontier Engineer Finder static site."""
import http.server
import os
import threading

import pytest
from playwright.sync_api import Page, expect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT, "site")
CSV_PATH = os.path.join(ROOT, "SampleTrainings.csv")

PORT = 8791


@pytest.fixture(scope="module")
def server():
    """Serve the site directory on localhost for the test session."""
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(("127.0.0.1", PORT), handler)
    httpd_thread = threading.Thread(
        target=httpd.serve_forever, daemon=True
    )
    os.chdir(SITE_DIR)
    httpd_thread.start()
    yield f"http://127.0.0.1:{PORT}/index.html"
    httpd.shutdown()


def _upload_csv(page: Page, server_url: str):
    """Navigate to the site and upload the sample CSV."""
    page.goto(server_url)
    file_input = page.locator("#fileInput")
    file_input.set_input_files(CSV_PATH)
    # Wait for results to appear
    page.wait_for_selector("#results", state="visible", timeout=10000)


def test_page_loads(page: Page, server: str):
    """Page loads and shows the upload area."""
    page.goto(server)
    expect(page.locator("h1")).to_have_text("Frontier Engineer Finder")
    expect(page.locator("#uploadArea")).to_be_visible()
    expect(page.locator("#results")).to_be_hidden()


def test_summary_stats(page: Page, server: str):
    """After upload, summary stats match expected values."""
    _upload_csv(page, server)
    expect(page.locator("#statActivities")).to_have_text("40,000")
    expect(page.locator("#statLearners")).to_have_text("10,178")


def test_all_three_certs(page: Page, server: str):
    """Table 1 shows the correct count of learners with all 3 certs."""
    _upload_csv(page, server)
    expect(page.locator("#statAll3")).to_have_text("5")
    expect(page.locator("#badgeAll3")).to_have_text("5")
    rows = page.locator("#tableAll3 tr")
    expect(rows).to_have_count(5)


def test_two_of_three_certs(page: Page, server: str):
    """Table 2 shows 100 unique learners with 2 of 3 certs."""
    _upload_csv(page, server)
    expect(page.locator("#stat2of3")).to_have_text("100")
    expect(page.locator("#badge2of3")).to_have_text("100")
    rows = page.locator("#table2of3 tr")
    expect(rows).to_have_count(100)


def test_at_risk(page: Page, server: str):
    """Table 3 shows the correct at-risk certifications count."""
    _upload_csv(page, server)
    # The at-risk count depends on "today" in the browser, which is
    # the actual current date. We computed 77 for 2026-05-04.
    # Just verify the table has rows and the stat is a number > 0.
    stat_text = page.locator("#statAtRisk").text_content()
    assert stat_text is not None
    at_risk_count = int(stat_text)
    assert at_risk_count > 0
    rows = page.locator("#tableAtRisk tr")
    expect(rows).to_have_count(at_risk_count)


def test_upload_hides_upload_area(page: Page, server: str):
    """After uploading, the upload area is hidden and results are shown."""
    _upload_csv(page, server)
    expect(page.locator("#uploadArea")).to_be_hidden()
    expect(page.locator("#results")).to_be_visible()


def test_file_name_displayed(page: Page, server: str):
    """The uploaded file name is displayed."""
    _upload_csv(page, server)
    expect(page.locator("#fileInfo")).to_contain_text("SampleTrainings.csv")


def test_no_network_requests_for_data(page: Page, server: str):
    """No network requests are made to upload the file data."""
    requests_made = []
    page.on("request", lambda req: requests_made.append(req.url))
    _upload_csv(page, server)
    # Only requests should be for page assets (html, papaparse CDN)
    data_uploads = [r for r in requests_made if "upload" in r.lower() or r.endswith(".csv")]
    assert len(data_uploads) == 0, f"Unexpected data upload requests: {data_uploads}"


def test_privacy_note_visible(page: Page, server: str):
    """The privacy note is visible after upload."""
    _upload_csv(page, server)
    expect(page.locator(".privacy-note")).to_contain_text("processed entirely in your browser")
