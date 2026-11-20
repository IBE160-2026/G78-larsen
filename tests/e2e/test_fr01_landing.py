"""Landing (FR-1, FR-22, FR-23, UX-DR4, UX-DR5, UX-DR15, UX-DR16): the rail with the Venue facts and Book seats in
the first view at 1366 x 768, the main column's sections in order with the copy verbatim, the Venue facts from the
seed, the title, axe, keyboard reach of every link and the button (through `a11y.tab_to` and `a11y.press`), no
horizontal scroll, `/#before-you-come` shown and focused, Book seats navigating, and the Notice while the backend
is stopped."""

from __future__ import annotations

import re

import httpx
from playwright.sync_api import Page

from . import a11y

DESCRIPTION = ("Löyly is the steam that rises when water meets the hot stones. At Saunalöyly you come to Finnish "
               "saunas by the sea, where you can swim all year round.")
SEAT_STATEMENT = ("A booking gives you seats in the shared saunas open during your session. On site you can move "
                  "freely between them.")
RULES = {
    "What to bring": ["Swimwear to wear at the venue.", "Two towels. One to sit on and one to dry yourself with.",
                      "A bottle for water."],
    "Safety": ["Drink enough water to avoid dehydration.", "Alcohol is not allowed at the venue.",
               "Keep rounds in the sauna to 10 minutes at most, and leave if you feel unwell.",
               "Ask the others before throwing water on the stones.",
               "Swim preferably with others, and never ice-bathe alone.", "Children must be supervised by an adult."],
    "Practical": ["Changing time is part of your session.", "There is a wardrobe for your clothes.",
                  "You can swim in the sea all year round.", "There are showers.",
                  "There is a tap with drinking water."],
}
SAUNAS = [
    ("Rauha", "Holds 7", "Rauha means peace.", "/images/sauna-rauha-door.jpg"),
    ("Löyly", "Holds 10", "Named for the steam from the stones, like the venue.", "/images/sauna-loyly-kiuas.jpg"),
    ("Kajo", "Holds 12", "Kajo means a soft glow of light.", "/images/sauna-kajo-kiulu.jpg"),
    ("Lumo", "Holds 15", "Lumo means enchantment.", "/images/sauna-lumo-lauteet.jpg"),
]
NOTICE = "The venue details could not be loaded, please try again."


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


def _lines(locator) -> list[str]:
    return [_norm(t) for t in locator.inner_text().splitlines() if t.strip()]


def test_title_is_the_venue_name(page: Page, base_url):
    page.goto(base_url + "/")
    assert page.title() == "Saunalöyly"


def test_rail_holds_the_wordmark_heading_the_facts_and_book_seats(page: Page, base_url):
    page.goto(base_url + "/")
    rail = page.locator(".rail")
    assert page.locator("h1").count() == 1
    h1 = rail.locator("h1")
    assert h1.inner_text() == "Saunalöyly"
    assert h1.locator("xpath=ancestor-or-self::a").count() == 0  # a heading, not a link
    assert _lines(rail) == ["Saunalöyly", "Open every day", "10:00–22:00", "Sessions last 1 h 30 min",
                            "NOK 250 per seat", "incl. VAT", "Book seats"]
    book = rail.get_by_role("link", name="Book seats", exact=True)
    assert book.get_attribute("href") == "/book-seats"
    assert page.locator(".notice").count() == 0


def test_rail_is_in_the_first_view_at_1366x768(page: Page, base_url):
    page.set_viewport_size({"width": 1366, "height": 768})
    page.goto(base_url + "/")
    for locator in (page.locator(".rail h1"), page.locator(".rail-fact").last,
                    page.get_by_role("link", name="Book seats", exact=True)):
        box = locator.bounding_box()
        assert box and box["y"] >= 0 and box["y"] + box["height"] <= 768, box


def test_main_holds_the_sections_top_to_bottom(page: Page, base_url):
    page.goto(base_url + "/")
    parts = page.evaluate("""() => Array.from(document.querySelectorAll('main > *')).map(el =>
        el.tagName === 'IMG' ? 'img:' + new URL(el.src).pathname
          : (el.querySelector('h2') ? el.querySelector('h2').textContent.trim() : el.className))""")
    assert parts == ["img:/images/hero-sauna-by-the-water.jpg", "venue-description", "Before you come", "The saunas",
                     "img:/images/band-loyly-steam.jpg", "Find us"]
    assert _norm(page.locator(".venue-description").inner_text()) == DESCRIPTION
    fi = page.locator("main [lang]")
    assert fi.count() == 1 and fi.get_attribute("lang") == "fi" and fi.inner_text() == "Löyly"
    ys = [page.locator(sel).bounding_box()["y"] for sel in
          (".hero", ".venue-description", "#before-you-come", ".saunas", ".band", ".find-us")]
    assert ys == sorted(ys)


def test_before_you_come_has_three_rule_lists_in_columns_then_one_image(page: Page, base_url):
    page.set_viewport_size({"width": 1366, "height": 768})
    page.goto(base_url + "/")
    section = page.locator("section#before-you-come")
    assert section.get_attribute("tabindex") == "-1"
    assert section.locator("h2").inner_text() == "Before you come"
    lists = section.locator(".rule-list")
    got = {lists.nth(i).locator("h3").inner_text(): [_norm(t) for t in lists.nth(i).locator("li").all_inner_texts()]
           for i in range(lists.count())}
    assert got == RULES
    assert list(got) == list(RULES)
    boxes = [lists.nth(i).bounding_box() for i in range(3)]
    assert len({round(b["y"]) for b in boxes}) == 1 and boxes[0]["x"] < boxes[1]["x"] < boxes[2]["x"]
    images = section.locator("img")
    assert images.count() == 1
    assert images.bounding_box()["y"] > max(b["y"] + b["height"] for b in boxes)
    # below 1200 px the columns stack
    page.set_viewport_size({"width": 1199, "height": 768})
    boxes = [lists.nth(i).bounding_box() for i in range(3)]
    assert boxes[0]["y"] < boxes[1]["y"] < boxes[2]["y"]
    assert len({round(b["x"]) for b in boxes}) == 1


def test_the_saunas_shows_the_seat_statement_and_four_cards(page: Page, base_url):
    page.goto(base_url + "/")
    section = page.locator("section.saunas")
    assert section.locator("h2").inner_text() == "The saunas"
    assert _norm(section.locator(".saunas-intro p").inner_text()) == SEAT_STATEMENT
    cards = section.locator(".sauna-card")
    got = []
    for i in range(cards.count()):
        card = cards.nth(i)
        img = card.locator("img")
        assert img.count() == 1 and img.get_attribute("alt")
        got.append((card.locator("h3").inner_text(), card.locator(".meta").inner_text(),
                    card.locator("p:not(.meta)").inner_text(), img.get_attribute("src")))
        # not a link and not selectable
        assert card.locator("a, button, input, [tabindex]").count() == 0
        assert card.evaluate("el => !el.closest('a, button, label, [role=radio], [role=option]')")
    assert got == SAUNAS


def test_find_us_shows_the_address_contact_and_the_two_links(page: Page, base_url):
    page.goto(base_url + "/")
    find = page.locator("section.find-us")
    assert _lines(find) == ["Find us", "Badstubrygga 4", "0000 Havbukta", "+47 01 23 45 67",
                            "hello@saunaloyly.example", "Terms", "Privacy notice"]
    assert find.get_by_role("link", name="Terms", exact=True).get_attribute("href") == "/terms"
    assert find.get_by_role("link", name="Privacy notice", exact=True).get_attribute("href") == "/privacy"


def test_every_image_is_a_plain_img_from_our_origin_with_alt_text_and_loads(page: Page, base_url):
    page.goto(base_url + "/")
    page.wait_for_load_state("networkidle")
    images = page.evaluate("""() => Array.from(document.images).map(i => ({
        src: i.currentSrc || i.src, alt: i.getAttribute('alt'), loaded: i.complete && i.naturalWidth > 0,
        srcset: i.getAttribute('srcset')}))""")
    assert len(images) == 7
    for img in images:
        assert img["src"].startswith(base_url + "/images/") and img["src"].endswith(".jpg"), img
        assert img["alt"] and len(img["alt"]) > 20, img
        assert img["loaded"], img
        assert img["srcset"] is None, img  # a plain <img>, not next/image


def test_axe_passes_and_no_horizontal_scroll(page: Page, base_url):
    page.goto(base_url + "/")
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_every_link_and_the_button_can_be_reached_with_the_keyboard(page: Page, base_url):
    page.goto(base_url + "/")
    links = page.locator("a")
    names = [_norm(n) for n in links.all_inner_texts()]
    assert sorted(names) == sorted(["Terms", "Privacy notice", "Book seats"])
    for name in names:
        page.goto(base_url + "/")
        a11y.tab_to(page, page.get_by_role("link", name=name, exact=True))


def test_book_seats_navigates_with_the_keyboard_and_sets_no_cookie(page: Page, base_url):
    page.goto(base_url + "/")
    a11y.tab_to(page, page.get_by_role("link", name="Book seats", exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/book-seats")
    # Story 1.4 builds the page; until then the route is the not-available page (Next.js loads an unknown route
    # as a new document, so focus there stays at the start of the page)
    assert page.locator("h1").inner_text() == "This page is not available."
    assert page.context.cookies() == []


def test_opening_before_you_come_directly_shows_and_focuses_it(page: Page, base_url):
    page.goto(base_url + "/#before-you-come")
    page.wait_for_function("() => document.activeElement && document.activeElement.id === 'before-you-come'")
    state = a11y.assert_focus_visible(page)
    assert state["tag"] == "section"
    box = page.locator("#before-you-come").bounding_box()
    assert box["y"] < page.viewport_size["height"] and box["y"] + box["height"] > 0
    assert page.context.cookies() == []


def test_venue_facts_through_caddy_need_no_session(base_url):
    r = httpx.get(base_url + "/api/venue", timeout=10)
    assert r.status_code == 200
    assert "set-cookie" not in r.headers
    body = r.json()
    assert body["name"] == "Saunalöyly" and body["price_per_seat_ore"] == 25000
    assert [s["name"] for s in body["saunas"]] == ["Rauha", "Löyly", "Kajo", "Lumo"]


def test_with_the_backend_stopped_landing_shows_the_notice_and_book_seats_works(stack, page: Page, base_url):
    stack.compose("stop", "backend")
    try:
        page.goto(base_url + "/")
        rail = page.locator(".rail")
        assert _lines(rail) == ["Saunalöyly", NOTICE, "Book seats"]
        # the main column keeps its copy; no Venue fact is shown
        assert _norm(page.locator(".venue-description").inner_text()) == DESCRIPTION
        assert page.locator("#before-you-come .rule-list").count() == 3
        assert page.locator(".sauna-card").count() == 0
        assert _lines(page.locator("section.find-us")) == ["Find us", "Terms", "Privacy notice"]
        text = _norm(page.locator("body").inner_text())
        for fact in ("NOK", "10:00", "1 h 30 min", "Holds", "Badstubrygga", "hello@saunaloyly.example"):
            assert fact not in text, fact
        page.get_by_role("link", name="Book seats", exact=True).click()
        page.wait_for_url(base_url + "/book-seats")
        assert page.locator("h1").inner_text() == "This page is not available."
    finally:
        stack.compose("start", "backend")
        stack.wait()
    assert httpx.get(base_url + "/api/health", timeout=10).status_code == 200
