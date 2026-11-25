"""Terms (FR-5) and the Privacy notice (FR-21) in the Guest shell, checked for look and accessibility (FR-22,
FR-23, UX-DR28, UX-DR33, UX-DR34): the mockups' text verbatim with h1 and h2, only the Wordmark in the rail,
page titles, axe, no horizontal scroll, 200 % zoom, and every link reached and followed with the keyboard alone
(through `a11y.tab_to` and `a11y.press`).

Back under the h1 (Lisa 2026-11-25): from a page of the site it goes back in the history, so Review comes back with
everything entered; opened directly it goes to Landing, and without JavaScript it is a link to Landing."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page

from . import a11y
from .test_fr05_book_and_pay import free_windows, open_session, review_draft, set_draft

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
    assert a11y.tab_order(page, 4) == [("link", "Back"), ("link", "Before you come"), ("link", "Privacy notice"),
                                       ("link", "Saunalöyly")]


def test_tab_order_on_privacy(page: Page, base_url):
    page.goto(base_url + "/privacy")
    assert a11y.tab_order(page, 3) == [("link", "Back"), ("link", "datatilsynet.no"), ("link", "Saunalöyly")]


# Each site link: (page, link name, where it leads, the focus target there). Following a link moves focus to the
# target page's h1 (AD-17); on Landing that is the Wordmark. A link to a fragment focuses that part instead.
SITE_LINKS = [
    ("/terms", "Back", "/", "Saunalöyly"),  # opened directly: Back goes to Landing
    ("/privacy", "Back", "/", "Saunalöyly"),
    ("/terms", "Before you come", "/#before-you-come", "#before-you-come"),
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
    if focus.startswith("#"):
        page.wait_for_function("id => document.activeElement && document.activeElement.id === id", arg=focus[1:])
        a11y.assert_focus_visible(page)
        return
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


# ------------------------------------------------------------------ Back (Lisa 2026-11-25)


def test_back_from_terms_and_the_privacy_notice_returns_to_review_with_everything_kept(page: Page, base_url):
    """Review -> Terms -> Privacy notice, then Back twice with the keyboard: Review again, from the draft, with the
    name, email and Seats as entered and the same key (AD-9)."""
    window = free_windows(base_url)[0]
    open_session(page, base_url)
    set_draft(page, review_draft(window, seats=3))
    page.goto(base_url + "/book-seats/review")
    page.get_by_role("button", name="Pay NOK 750").wait_for()
    key = page.evaluate("JSON.parse(sessionStorage.getItem('draft:seats')).key")
    a11y.tab_to(page, page.locator(".terms-section").get_by_role("link", name="Terms", exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/terms")
    a11y.tab_to(page, page.locator("main").get_by_role("link", name="Privacy notice", exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/privacy")
    for back_to in ("/terms", "/book-seats/review"):
        a11y.tab_to(page, page.get_by_role("link", name="Back", exact=True))
        a11y.press(page, "Enter")
        page.wait_for_url(base_url + back_to)
    page.get_by_role("button", name="Pay NOK 750").wait_for()
    page.wait_for_function("() => { const el = document.activeElement; "
                           "return el && el.tagName === 'H1' && el.textContent.trim() === 'Review'; }")
    rows = [_norm(t) for t in page.locator(".summary-row").all_inner_texts()]
    assert "Seats 3 seats" in rows and "Name Ingrid Hansen" in rows and "Email ingrid@example.com" in rows, rows
    assert page.evaluate("JSON.parse(sessionStorage.getItem('draft:seats')).key") == key


@pytest.mark.parametrize("path", PAGES)
def test_back_is_a_link_to_landing_without_javascript(browser: Browser, base_url, path):
    context = browser.new_context(java_script_enabled=False, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(base_url + path)
        back = page.locator("main .back").get_by_role("link", name="Back", exact=True)
        assert back.get_attribute("href") == "/"
        back.click()
        page.wait_for_url(base_url + "/")
    finally:
        context.close()


def test_without_the_navigation_api_back_still_returns_to_the_page_it_came_from(page: Page, base_url):
    """The fallback for browsers without `window.navigation` (Firefox, older Safari): a client navigation in this
    document (lib/nav.js) means Back goes back; a direct open goes to Landing."""
    page.add_init_script("try { Object.defineProperty(window, 'navigation', {value: undefined, configurable: true}); "
                         "} catch (e) {}")
    page.goto(base_url + "/terms")
    assert page.evaluate("typeof window.navigation") == "undefined"
    page.get_by_role("link", name="Back", exact=True).click()  # opened directly
    page.wait_for_url(base_url + "/")
    page.locator("main").get_by_role("link", name="Terms", exact=True).click()
    page.wait_for_url(base_url + "/terms")
    page.locator("main").get_by_role("link", name="Privacy notice", exact=True).click()
    page.wait_for_url(base_url + "/privacy")
    page.get_by_role("link", name="Back", exact=True).click()  # came from Terms
    page.wait_for_url(base_url + "/terms")
