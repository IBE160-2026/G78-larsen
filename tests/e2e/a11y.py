"""The shared accessibility helper of the e2e layer (FR-22, FR-23, UX-DR34).

Every keyboard step "with the keyboard alone", in this story and every later one, goes through `press` and
`tab_to`, so focus visibility is checked after every key press and not first in Story 2.4.

- `check_axe(page)`: axe-core from `frontend/node_modules`, no WCAG level A or AA failure.
- `no_horizontal_scroll(page)`: at 1024, 1366 and 1920 px wide.
- `press(page, key)` and `tab_to(page, locator)`: after every key press, the focused element shows the 3 px focus
  ring (its computed outline) and is not hidden: inside the viewport and the topmost element at its centre.
- `tab_order(page, steps)`: the focus stops in order, as (role, accessible name).
- `zoomed(browser, width, height)`: a page laid out as at 200 % browser zoom (WCAG 1.4.4).
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Browser, Locator, Page

ROOT = Path(__file__).resolve().parents[2]
AXE = ROOT / "frontend" / "node_modules" / "axe-core" / "axe.min.js"

# WCAG 2.2 A and AA, as axe tags them.
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"]
# The one known gap (FR-23): 1.4.10 Reflow, until the narrow layout of FR-51. axe tags it `wcag1410`.
KNOWN_GAPS = {"wcag1410": "1.4.10 Reflow (until FR-51)"}

WIDTHS = {1024: 768, 1366: 768, 1920: 1080}

FOCUS_WIDTH = "3px"
FOCUS_COLOR = "rgb(47, 90, 113)"  # --color-focus #2F5A71

_FOCUS_STATE = """() => {
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement) return {focused: false};
  el.scrollIntoView({block: 'nearest', inline: 'nearest'});
  const s = getComputedStyle(el);
  // the first box of the element: a link that wraps has a gap at the centre of its bounding box
  const r = el.getClientRects()[0] || el.getBoundingClientRect();
  const vw = document.documentElement.clientWidth, vh = document.documentElement.clientHeight;
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const inside = r.width > 0 && r.height > 0 && cx >= 0 && cy >= 0 && cx <= vw && cy <= vh;
  const top = inside ? document.elementFromPoint(cx, cy) : null;
  return {
    focused: true,
    tag: el.tagName.toLowerCase(),
    text: (el.textContent || '').trim().slice(0, 60),
    outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth, outlineColor: s.outlineColor,
    inside,
    topmost: !!top && (top === el || el.contains(top)),
  };
}"""


def _focus_state(page: Page, timeout: float = 3.0) -> dict:
    """The focused element's state. A key press may start a navigation, so this waits (briefly) until some
    element other than the body has focus and its ring is drawn."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            state = page.evaluate(_FOCUS_STATE)
        except Exception:  # the page navigated while evaluating
            state = {"focused": False}
        ok = state.get("focused") and state.get("outlineStyle") != "none"
        if ok or time.monotonic() > deadline:
            return state
        page.wait_for_timeout(50)


def assert_focus_visible(page: Page) -> dict:
    state = _focus_state(page)
    assert state.get("focused"), "no element has focus after the key press"
    where = f"<{state['tag']}> {state['text']!r}"
    assert state["outlineStyle"] != "none" and state["outlineWidth"] == FOCUS_WIDTH, \
        f"{where} shows no 3 px focus ring (outline {state['outlineStyle']} {state['outlineWidth']})"
    assert state["outlineColor"] == FOCUS_COLOR, f"{where} focus ring is {state['outlineColor']}, not the focus token"
    assert state["inside"], f"{where} is outside the viewport"
    assert state["topmost"], f"{where} is covered by another element"
    return state


def press(page: Page, key: str) -> None:
    """Press one key, then assert that focus is visible (WCAG 2.4.7, 2.4.11)."""
    page.keyboard.press(key)
    assert_focus_visible(page)


def _is_focused(locator: Locator) -> bool:
    return locator.evaluate("el => el === document.activeElement")


def tab_to(page: Page, locator: Locator, max_steps: int = 60) -> None:
    """Press Tab (each through `press`) until `locator` has focus."""
    for _ in range(max_steps):
        press(page, "Tab")
        if _is_focused(locator):
            return
    raise AssertionError(f"{locator} was not reached in {max_steps} Tab presses")


_ROLE_AND_NAME = """() => {
  const el = document.activeElement;
  const tag = el.tagName.toLowerCase();
  const implicit = {a: el.hasAttribute('href') ? 'link' : null, button: 'button', select: 'combobox',
                    textarea: 'textbox', summary: 'button', h1: 'heading', h2: 'heading', h3: 'heading'};
  let role = el.getAttribute('role') || implicit[tag] || null;
  if (!role && tag === 'input') {
    const t = (el.getAttribute('type') || 'text').toLowerCase();
    role = {checkbox: 'checkbox', radio: 'radio', button: 'button', submit: 'button'}[t] || 'textbox';
  }
  let name = el.getAttribute('aria-label');
  if (!name && el.getAttribute('aria-labelledby')) {
    name = el.getAttribute('aria-labelledby').split(/\\s+/)
      .map(id => (document.getElementById(id) || {}).textContent || '').join(' ');
  }
  if (!name && el.labels && el.labels.length) name = el.labels[0].textContent;
  if (!name) name = el.textContent;
  return [role || tag, (name || '').replace(/\\s+/g, ' ').trim()];
}"""


def tab_order(page: Page, steps: int) -> list[tuple[str, str]]:
    """Press Tab `steps` times (each through `press`) and return the focus stops as (role, accessible name)."""
    stops = []
    for _ in range(steps):
        press(page, "Tab")
        role, name = page.evaluate(_ROLE_AND_NAME)
        stops.append((role, name))
    return stops


def check_axe(page: Page) -> None:
    """Run axe-core on the page; no WCAG 2.2 level A or AA failure other than the known gap."""
    page.add_script_tag(path=str(AXE))
    result = page.evaluate("tags => axe.run(document, {runOnly: {type: 'tag', values: tags}})", AXE_TAGS)
    failures = [v for v in result["violations"] if not set(v["tags"]) & set(KNOWN_GAPS)]
    assert not failures, "axe: " + "; ".join(
        f"{v['id']} ({v['impact']}): {[n['target'] for n in v['nodes']][:5]}" for v in failures)


def no_horizontal_scroll(page: Page) -> None:
    """No horizontal scrolling at 1024, 1366 and 1920 px wide (FR-22)."""
    original = page.viewport_size
    try:
        for width, height in WIDTHS.items():
            page.set_viewport_size({"width": width, "height": height})
            scroll, client = page.evaluate(
                "() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            assert scroll <= client, f"horizontal scroll at {width} px: content is {scroll} px wide, view {client} px"
    finally:
        if original:
            page.set_viewport_size(original)


@contextmanager
def zoomed(browser: Browser, width: int, height: int):
    """A page in its own context, laid out as at 200 % browser zoom on a `width` x `height` screen: a viewport of
    half the width and height with `deviceScaleFactor` 2 (WCAG 1.4.4)."""
    context = browser.new_context(viewport={"width": width // 2, "height": height // 2}, device_scale_factor=2)
    try:
        yield context.new_page()
    finally:
        context.close()
