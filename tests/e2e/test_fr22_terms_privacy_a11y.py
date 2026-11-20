"""Terms (FR-5) and the Privacy notice (FR-21) in the Guest shell, checked for look and accessibility (FR-22,
FR-23, UX-DR28, UX-DR33, UX-DR34): the mockups' text verbatim with h1 and h2, only the Wordmark in the rail,
page titles, axe, no horizontal scroll, 200 % zoom, and every link reached and followed with the keyboard alone
(through `a11y.tab_to` and `a11y.press`)."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page

from . import a11y

MOCKUPS = (Path(__file__).resolve().parents[2] / ".docs" / "planning-artifacts" / "ux-designs"
           / "ux-booking-platform-2026-11-05" / "mockups")

PAGES = {
    "/terms": {"mockup": "key-terms.html", "h1": "Booking terms", "first": "Who we are", "last": "Your data"},
    "/privacy": {"mockup": "key-privacy.html", "h1": "Privacy notice", "first": "Who is responsible",
                 "last": "Your rights"},
}


class _MockupText(HTMLParser):
    """The text blocks (headings and paragraphs) inside the mockup's main column `<div class="col">`."""

    def __init__(self):
        super().__init__()
        self.depth = 0  # depth inside div.col, 0 = outside
        self.block: list[str] | None = None
        self.blocks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == "div":
                self.depth += 1
            if tag in ("h2", "h3", "p"):
                self.block = []
        elif tag == "div" and ("class", "col") in attrs:
            self.depth = 1

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ("h2", "h3", "p") and self.block is not None:
            self.blocks.append("".join(self.block))
            self.block = None
        elif tag == "div":
            self.depth -= 1

    def handle_data(self, data):
        if self.block is not None:
            self.block.append(data)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


def mockup_blocks(name: str) -> list[str]:
    parser = _MockupText()
    parser.feed((MOCKUPS / name).read_text(encoding="utf-8"))
    return [_norm(b) for b in parser.blocks]


@pytest.mark.parametrize("path", PAGES)
def test_full_text_of_the_mockup_with_h1_and_h2(page: Page, base_url, path):
    spec = PAGES[path]
    page.goto(base_url + path)
    blocks = [_norm(t) for t in page.locator("main article").locator("h1, h2, p").all_inner_texts()]
    assert blocks == mockup_blocks(spec["mockup"])
    assert page.locator("h1").all_inner_texts() == [spec["h1"]]
    h2 = page.locator("main h2").all_inner_texts()
    assert h2[0] == spec["first"] and h2[-1] == spec["last"]
    assert page.locator("h3").count() == 0
    assert page.title() == f"{spec['h1']} – Saunalöyly"


def test_privacy_notice_states_what_fr21_requires(page: Page, base_url):
    page.goto(base_url + "/privacy")
    text = _norm(page.locator("main").inner_text())
    for fact in ("data controller", "hello@saunaloyly.example", "What we store and why", "Legal basis",
                 "GDPR art. 6(1)(b)", "How long we keep it", "12 months", "Who sees your data", "Your rights",
                 "Datatilsynet", "How we protect it"):
        assert fact in text, fact


@pytest.mark.parametrize("path", PAGES)
def test_the_rail_shows_only_the_wordmark(page: Page, base_url, path):
    page.goto(base_url + path)
    rail = page.locator(".rail")
    assert _norm(rail.inner_text()) == "Saunalöyly"
    assert rail.locator("a").count() == 1
    assert rail.locator("a").get_attribute("href") == "/"


@pytest.mark.parametrize("path", [*PAGES, "/", "/nope"])
def test_axe_passes(page: Page, base_url, path):
    page.goto(base_url + path)
    a11y.check_axe(page)


@pytest.mark.parametrize("path", PAGES)
def test_no_horizontal_scroll(page: Page, base_url, path):
    page.goto(base_url + path)
    a11y.no_horizontal_scroll(page)


@pytest.mark.parametrize("path", PAGES)
@pytest.mark.parametrize("screen", [(1366, 768), (1920, 1080)])
def test_200_percent_zoom_keeps_everything_reachable(browser: Browser, base_url, path, screen):
    with a11y.zoomed(browser, *screen) as page:
        page.goto(base_url + path)
        a11y.check_axe(page)
        links = page.locator("a")
        stops = a11y.tab_order(page, links.count())
        assert [role for role, _ in stops] == ["link"] * links.count()


def test_tab_order_on_terms(page: Page, base_url):
    page.goto(base_url + "/terms")
    assert a11y.tab_order(page, 3) == [("link", "Before you come"), ("link", "Privacy notice"),
                                       ("link", "Saunalöyly")]


def test_tab_order_on_privacy(page: Page, base_url):
    page.goto(base_url + "/privacy")
    assert a11y.tab_order(page, 2) == [("link", "datatilsynet.no"), ("link", "Saunalöyly")]


# Each site link: (page, link name, where it leads, the focus target there). Following a link moves focus to the
# target page's h1 (AD-17); on Landing that is the Wordmark.
SITE_LINKS = [
    ("/terms", "Before you come", "/#before-you-come", "Saunalöyly"),
    ("/terms", "Privacy notice", "/privacy", "Privacy notice"),
    ("/terms", "Saunalöyly", "/", "Saunalöyly"),
    ("/privacy", "Saunalöyly", "/", "Saunalöyly"),
    ("/", "Terms", "/terms", "Booking terms"),
    ("/", "Privacy notice", "/privacy", "Privacy notice"),
    ("/nope", "Go to the Saunalöyly start page", "/", "Saunalöyly"),
]


@pytest.mark.parametrize(("start", "name", "lands", "focus"), SITE_LINKS)
def test_every_link_can_be_reached_and_followed_with_the_keyboard(page: Page, base_url, start, name, lands, focus):
    page.goto(base_url + start)
    a11y.tab_to(page, page.get_by_role("link", name=name, exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + lands)
    page.wait_for_function("t => { const el = document.activeElement; "
                           "return el && el.tagName === 'H1' && el.textContent.trim() === t; }", arg=focus)
    state = a11y.assert_focus_visible(page)
    assert state["tag"] == "h1"


def test_the_external_link_is_followed_without_leaving_the_test_offline(page: Page, base_url):
    """Datatilsynet's link is reached and pressed; the navigation is caught, so the test makes no third-party
    request (FR-21)."""
    followed = []

    def catch(route):
        followed.append(route.request.url)
        route.fulfill(status=204)  # a 204 ends the navigation, so the page and its focus stay

    page.route("https://www.datatilsynet.no/**", catch)
    page.goto(base_url + "/privacy")
    a11y.tab_to(page, page.get_by_role("link", name="datatilsynet.no"))
    a11y.press(page, "Enter")
    page.wait_for_timeout(300)
    assert followed and followed[0].startswith("https://www.datatilsynet.no/")


def test_first_load_leaves_focus_alone_without_a_fragment(page: Page, base_url):
    page.goto(base_url + "/terms")
    page.wait_for_load_state("networkidle")
    # hydrated: React has attached its fiber to the h1; then let passive effects (the FocusMover) flush
    page.wait_for_function("() => { const h = document.querySelector('h1'); "
                           "return !!h && Object.keys(h).some(k => k.startsWith('__reactFiber')); }")
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 50))))")
    assert page.evaluate("document.activeElement === document.body")


def test_first_load_focuses_an_existing_fragment_target(page: Page, base_url):
    page.goto(base_url + "/privacy#main")
    page.wait_for_function("document.activeElement && document.activeElement.id === 'main'")
