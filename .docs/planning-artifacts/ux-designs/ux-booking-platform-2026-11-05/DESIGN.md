---
name: Saunalöyly Booking Platform
status: final
updated: 2026-11-09
description: Calm, plain booking website for one fictional Finnish sauna venue. Open Guide direction, light mode, one stylesheet with CSS custom properties, no UI library.
colors:
  page: '#F5F3EB'
  surface: '#FDFCF7'
  text: '#26353D'
  muted: '#4C5D66'
  primary: '#B5D2E1'
  on-primary: '#1E2D35'
  button-edge: '#26353D'
  bar: '#B5D2E1'
  on-bar: '#1E2D35'
  link: '#2F5A71'
  focus: '#2F5A71'
  border: '#6F8693'
  unavailable: '#E4EBEC'
  error: '#7F3C2E'
  success: '#2E6047'
typography:
  wordmark:
    fontFamily: Finlandica
    fontSize: 52px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.01em
  heading-xl:
    fontFamily: Finlandica
    fontSize: 44px
    fontWeight: '400'
    lineHeight: '1.12'
  heading-lg:
    fontFamily: Finlandica
    fontSize: 32px
    fontWeight: '400'
    lineHeight: '1.2'
  heading-md:
    fontFamily: Finlandica
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.25'
  lead:
    fontFamily: Source Sans 3
    fontSize: 30px
    fontWeight: '300'
    lineHeight: '1.3'
  body:
    fontFamily: Source Sans 3
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.65'
  body-sm:
    fontFamily: Source Sans 3
    fontSize: 17px
    fontWeight: '400'
    lineHeight: '1.45'
  small:
    fontFamily: Source Sans 3
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label:
    fontFamily: Source Sans 3
    fontSize: 15px
    fontWeight: '600'
    lineHeight: '1.3'
  hint:
    fontFamily: Source Sans 3
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
  button:
    fontFamily: Source Sans 3
    fontSize: 17px
    fontWeight: '600'
    lineHeight: '1.3'
  total:
    fontFamily: Source Sans 3
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.35'
  total-note:
    fontFamily: Source Sans 3
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.35'
  session-time:
    fontFamily: Source Sans 3
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.3'
  session-time-selected:
    fontFamily: Source Sans 3
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.3'
  calendar-day:
    fontFamily: Source Sans 3
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1'
  calendar-day-selected:
    fontFamily: Source Sans 3
    fontSize: 15px
    fontWeight: '700'
    lineHeight: '1'
rounded:
  none: 0px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 18px
  '5': 24px
  '6': 32px
  '7': 40px
  '8': 48px
  '9': 56px
  '10': 72px
  '11': 96px
  rail-width: 320px
  date-column: 348px
  before-image-height: 300px
  page-max: 1320px
  measure-text: 640px
  measure-lead: 800px
  hero-height: 468px
  sauna-image-height: 320px
  band-height: 220px
  button-height: 48px
  control-height: 44px
  session-row-height: 40px
  calendar-cell-height: 34px
  gutter-narrow: 16px
components:
  primary-button:
    background: '{colors.primary}'
    foreground: '{colors.on-primary}'
    border: '1.5px solid {colors.button-edge}'
    radius: '{rounded.none}'
    type: '{typography.button}'
    minHeight: '{spacing.button-height}'
    paddingInline: '{spacing.5}'
  text-link:
    foreground: '{colors.link}'
    decoration: underline
  wordmark:
    foreground: '{colors.text}'
    type: '{typography.wordmark}'
    marginBottom: '{spacing.5}'
  rail:
    background: '{colors.page}'
    width: '{spacing.rail-width}'
    paddingBlock: '{spacing.6}'
    paddingInline: '{spacing.7}'
  text-field:
    background: '{colors.surface}'
    foreground: '{colors.text}'
    border: '1px solid {colors.border}'
    radius: '{rounded.none}'
    type: '{typography.body-sm}'
    height: '{spacing.control-height}'
  terms-checkbox:
    accent: '{colors.link}'
    size: 16px
    type: '{typography.body-sm}'
  date-calendar:
    background: '{colors.surface}'
    border: '1px solid {colors.border}'
    type: '{typography.calendar-day}'
    height: '{spacing.calendar-cell-height}'
    gap: '{spacing.1}'
  date-calendar-selected:
    background: '{colors.primary}'
    foreground: '{colors.on-primary}'
    border: '1.5px solid {colors.button-edge}'
    type: '{typography.calendar-day-selected}'
  date-calendar-unavailable:
    background: '{colors.unavailable}'
    foreground: '{colors.muted}'
    border: none
  seat-picker:
    background: '{colors.surface}'
    border: '1px solid {colors.border}'
    type: '{typography.body-sm}'
    height: '{spacing.control-height}'
    gap: '{spacing.1}'
  seat-picker-selected:
    background: '{colors.primary}'
    foreground: '{colors.on-primary}'
    border: '1.5px solid {colors.button-edge}'
    fontWeight: '700'
  session-row:
    borderTop: '1px solid {colors.border}'
    type: '{typography.body-sm}'
    timeType: '{typography.session-time}'
    minHeight: '{spacing.session-row-height}'
    paddingInline: '{spacing.3}'
  session-row-selected:
    background: '{colors.surface}'
    bar: 'inset 3px 0 0 {colors.button-edge}'
    timeType: '{typography.session-time-selected}'
    fontWeight: '600'
  session-row-unavailable:
    background: '{colors.unavailable}'
  total-block:
    type: '{typography.total}'
    noteType: '{typography.total-note}'
    noteForeground: '{colors.muted}'
    marginBottom: '{spacing.3}'
  rail-note:
    foreground: '{colors.muted}'
    type: '{typography.body-sm}'
    marginTop: '{spacing.4}'
  fixed-action-bar:
    background: '{colors.surface}'
    borderTop: '1px solid {colors.border}'
    padding: '{spacing.3}'
  image-block:
    radius: '{rounded.none}'
  rule-list:
    titleBorderBottom: '1px solid {colors.border}'
    paddingBlock: '{spacing.2}'
  sauna-card:
    imageHeight: '{spacing.sauna-image-height}'
    nameType: '{typography.heading-lg}'
    metaForeground: '{colors.muted}'
  find-us-block:
    borderTop: '1px solid {colors.border}'
    type: '{typography.small}'
    gap: '{spacing.6}'
  notice:
    background: '{colors.surface}'
    border: '1px solid {colors.border}'
    padding: '{spacing.3}'
  error-summary:
    background: '{colors.surface}'
    foreground: '{colors.error}'
    border: '1px solid {colors.error}'
    padding: '{spacing.3}'
  field-error:
    foreground: '{colors.error}'
    type: '{typography.hint}'
  booking-summary:
    borderTop: '1px solid {colors.border}'
    type: '{typography.body}'
  reference-display:
    type: '{typography.heading-lg}'
    foreground: '{colors.text}'
  email-as-sent:
    background: '{colors.surface}'
    border: '1px solid {colors.border}'
    type: '{typography.small}'
    padding: '{spacing.5}'
  administrator-bar:
    background: '{colors.bar}'
    foreground: '{colors.on-bar}'
    paddingBlock: '{spacing.3}'
    paddingInline: '{spacing.5}'
  session-group:
    borderTop: '1px solid {colors.border}'
    timeType: '{typography.heading-md}'
    figureType: '{typography.body-sm}'
  booking-table:
    rowBorder: '1px solid {colors.border}'
    type: '{typography.body-sm}'
    headerType: '{typography.label}'
  outbox-entry:
    background: '{colors.surface}'
    border: '1px solid {colors.border}'
    type: '{typography.small}'
    padding: '{spacing.5}'
---

# Saunalöyly Booking Platform: Design Spine

## Brand & Style

The website should feel like the sauna it sells: calm, honest and plain. The Finnish word is *saunarauha*, the peace of the sauna. Nothing on the page pushes. Facts come before persuasion, and the wish to visit comes from the place itself, through imagery and quiet space, not from emotive copy. A guest should come away looking forward to unwinding, and should have been told nothing they did not need.

The direction is **Open Guide**: the opening is image-led and airy, the text then runs like a printed leaflet, and the left margin that holds the name also holds the one action. Because that margin stays in view, nothing has to be said twice. Booking itself is a sheet of paper with three questions on it. Anything that reads as a spa brochure, a sales funnel or a boast about heat is wrong for this product.

This spine holds visual identity. Behaviour, copy and the home of each fact live in `EXPERIENCE.md`. UI system: none. Everything is built from these tokens in one stylesheet with CSS custom properties.

Light mode only. [ASSUMPTION] No dark tokens are defined, because only light values were chosen (memlog).

## Colors

The palette is pale sky on warm paper, with one dark ink. Every token below is final (variant A, [`color-themes-3.html`](mockups/color-themes-3.html)). The PRD's light wood and forest green reach the page through the photographs, not through the interface.

- **Page (`#F5F3EB`)** is the warm paper background of every guest page, and of the rail.
- **Surface (`#FDFCF7`)** sits on the page wherever something needs to lift slightly: input fields, calendar days, seat buttons, the selected Session row, notices. The step from page is only 1.1:1, so surface never carries meaning alone.
- **Text (`#26353D`)** is the dark grey-blue ink for all reading text.
- **Muted (`#4C5D66`)** is for secondary text: rail notes, hints, meta lines such as a Sauna's size. It passes AA on every background, so a required statement may sit in it.
- **Primary (`#B5D2E1`)** is the sky blue of the one action on a page, and of a selected date or seat count. **On-primary (`#1E2D35`)** is its text.
- **Button edge (`#26353D`)** is what makes primary fill visible at all. Primary on page is only 1.4:1, so the edge is required, not decoration.
- **Bar (`#B5D2E1`)** and **On-bar (`#1E2D35`)** share primary's values and are separate tokens so the bar can change alone. Open Guide has no bar on guest pages. [ASSUMPTION] The bar is used for the Administrator bar only, because it is the one chosen token with no guest use and it marks staff pages as different.
- **Link (`#2F5A71`)** is for underlined text links. **Focus (`#2F5A71`)** shares the value and is used only for the focus ring.
- **Border (`#6F8693`)** is the single line colour, used for field edges, rows and section rules. It clears 3:1 against page, surface and unavailable.
- **Unavailable (`#E4EBEC`)** marks days and Sessions that cannot be chosen. It is always paired with text or a missing control, because the fill alone is only 1.1:1 against page.
- **Error (`#7F3C2E`)** is for form and payment errors only. "Sold out" and no-room states are availability information and never use it.
- **Success (`#2E6047`)** is for the confirmed state only.

The flat tones in the mock (forest, granite, light wood, pine, birch, sea-blue) are image stand-ins. They are not tokens and appear nowhere in the product.

**Contrast, computed against WCAG 2.2 AA:**

| Pair | Ratio | Need |
|---|---|---|
| `{colors.text}` on `{colors.surface}` / `{colors.page}` / `{colors.unavailable}` | 12.3 / 11.4 / 10.5 | 4.5 |
| `{colors.muted}` on `{colors.surface}` / `{colors.page}` / `{colors.unavailable}` | 6.7 / 6.2 / 5.7 | 4.5 |
| `{colors.on-primary}` on `{colors.primary}`, `{colors.on-bar}` on `{colors.bar}` | 8.9 | 4.5 |
| `{colors.link}` on `{colors.surface}` / `{colors.page}` / `{colors.unavailable}` | 7.2 / 6.7 / 6.2 | 4.5 |
| `{colors.error}` on `{colors.surface}` / `{colors.page}` | 7.9 / 7.3 | 4.5 |
| `{colors.success}` on `{colors.surface}` / `{colors.page}` | 7.1 / 6.6 | 4.5 |
| `{colors.button-edge}` on `{colors.primary}` / `{colors.page}` | 8.0 / 11.4 | 3 |
| `{colors.focus}` on `{colors.page}` / `{colors.surface}` / `{colors.primary}` | 6.7 / 7.2 / 4.7 | 3 |
| `{colors.border}` on `{colors.surface}` / `{colors.page}` / `{colors.unavailable}` | 3.7 / 3.4 / 3.2 | 3 |

Fills that do not reach 3:1, so they must never be the only cue: `{colors.primary}` on page (1.4), `{colors.unavailable}` on page (1.1), `{colors.surface}` on page (1.1).

## Typography

**Finlandica** for headings and **Source Sans 3** for text, as in PRD §6. Both are under the SIL Open Font License and self-hosted in `frontend/public/` (no third-party requests, FR-21), and both are listed in `ASSETS.md` (DR-3). The mock's system font is only a stand-in.

**Weights are limited by the fonts.** Finlandica's weight axis runs from 400 to 700. The mock's headings are set at 300, which Finlandica does not have, so every Finlandica role here is 400, the lightest that exists. Headings will read a little firmer than in the mock. Source Sans 3 runs from 200 to 900, so its 300, 400, 600 and 700 are kept as rendered.

| Role | Token | Size / line height | Used for |
|---|---|---|---|
| Wordmark | `{typography.wordmark}` | 52 / 1.1, -0.01em | The name in the rail |
| Page and section heading | `{typography.heading-xl}` | 44 / 1.12 | "Book seats", "Before you come", "The saunas" |
| Large heading | `{typography.heading-lg}` | 32 / 1.2 | Sauna names, "Find us" |
| Small heading | `{typography.heading-md}` | 24 / 1.25 | What to bring, Safety, Practical; the numbered questions on Book seats, as `legend` |
| Lead | `{typography.lead}` | 30 / 1.3, weight 300 | Venue description under the hero |
| Body | `{typography.body}` | 18 / 1.65 | Reading text |
| Small body | `{typography.body-sm}` | 17 / 1.45 | Rail facts and notes, Session row text, input text, tables |
| Small | `{typography.small}` | 16 / 1.5 | "Find us" text, month name, email bodies |
| Label | `{typography.label}` | 15 / 1.3, weight 600 | Field labels, table headers |
| Hint | `{typography.hint}` | 14 / 1.4 | Hints under fields, field errors |
| Button | `{typography.button}` | 17 / 1.3, weight 600 | Primary button |
| Total | `{typography.total}` | 24 / 1.35, weight 600 | The total in the rail |
| Total note | `{typography.total-note}` | 15 / 1.35 | Price per seat under the total |
| Session time | `{typography.session-time}` | 18 / 1.3, weight 400 | Start and end in a Session row |
| Session time, selected | `{typography.session-time-selected}` | 18 / 1.3, weight 600 | The chosen Session |
| Calendar day | `{typography.calendar-day}` | 15 / 1 | Calendar days and weekday heads (heads in weight 600) |
| Calendar day, selected | `{typography.calendar-day-selected}` | 15 / 1, weight 700 | The chosen date |

[ASSUMPTION] The mock uses one font, so the split into two families is inferred: the numbered questions count as headings, while the lead and the Session times count as text. Reason: PRD §6 assigns fonts by role, and the times need tabular figures.

Times, dates and seat counts use tabular figures (`font-variant-numeric: tabular-nums`). Confirm that the self-hosted Source Sans 3 file keeps this feature after subsetting. Both fonts must include ö.

[ASSUMPTION] Fallback stack: `system-ui, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`, the mock's stand-in stack, used only until the self-hosted files load.

## Layout & Spacing

**Scale:** 4, 8, 12, 18, 24, 32, 40, 48, 56, 72, 96 px (`{spacing.1}` to `{spacing.11}`). [ASSUMPTION] The mock's near-duplicate values are folded onto this scale so one stylesheet stays readable: 3 and 5 become 4, 7 becomes 8, 14 becomes 12, 26 becomes 24, 30 and 34 become 32, 104 becomes 96. No fold changes more than 2 px except 104 to 96, which is on the Landing page only.

**The shell.** Two columns on every guest page: a fixed `{spacing.rail-width}` rail on the left and a fluid main column. The rail is its own column and is sticky, so nothing ever scrolls under it and focus can never be hidden by it. There is no line between rail and main; they share `{colors.page}`. [ASSUMPTION] The shell stops at `{spacing.page-max}`, centred, at 1920 × 1080. This is the only width the direction was rendered at, and no wider layout was reviewed.

Rail padding is `{spacing.6}` top and bottom and `{spacing.7}` at the sides. The main column's side gutter is `{spacing.9}`.

**Landing page, top to bottom in main:**

| Part | Geometry |
|---|---|
| Hero image | Full width of main, `{spacing.hero-height}` high, no inset |
| Venue description | `{typography.lead}`, top gap `{spacing.6}`, side gutter `{spacing.9}`, max width `{spacing.measure-lead}` |
| Before you come | Top gap `{spacing.11}`. Heading, then three equal columns, one per Rule list (What to bring, Safety, Practical), `{spacing.5}` under the heading, gap `{spacing.7}`, side gutter `{spacing.9}`. Under the columns, after `{spacing.7}`, one image `{spacing.before-image-height}` high, from the left text edge to the right edge of main (Lisa, 2026-11-09). Below 1200 px the columns stack (`EXPERIENCE.md`, Responsive & Platform) |
| The saunas | Padding `{spacing.11}` top and bottom. Intro text max width `{spacing.measure-text}`. Two-column grid, gaps `{spacing.8}` by `{spacing.7}`. Even cards start `{spacing.10}` lower, which gives the page its loose, unruled rhythm |
| Image band | Width of main less a `{spacing.9}` left inset, as the Before you come image, `{spacing.band-height}` high |
| Find us | Three equal columns, gap `{spacing.6}`, padding `{spacing.6}` top and `{spacing.7}` bottom |

The hero plus the first lines of the description fill the first view at 1366 × 768, taken as about 620 px of page height after browser chrome. The Book seats action is in that view without scrolling.

**Book seats page.** Main padding is `{spacing.5}` top and bottom and `{spacing.9}` at the sides. Under the heading are two columns: `{spacing.date-column}` for the date and fluid for seats and Sessions, gap `{spacing.8}`. The numbered questions sit `{spacing.2}` above their control, and question 3 sits `{spacing.4}` under the seat buttons.

The page is built to fit: heading, calendar, ten seat buttons and all eight seed Sessions come to about 570 px, so at 1366 × 768 a guest sees every step and the total without scrolling. Any new element on this page has to be checked against that budget. An Error summary is the exception: it appears only after Continue, the page may then scroll, and Continue stays in view in the rail.

**Other guest pages.** Details, Review, Confirmation, Terms and Privacy notice use the same shell with only the Wordmark in the rail. All but Review have a main column at `{spacing.measure-text}`. [Details](mockups/key-details.html), [Review](mockups/key-review.html), [Confirmation](mockups/key-confirmation.html), [Terms](mockups/key-terms.html) and [Privacy notice](mockups/key-privacy.html) are rendered.

**Review.** Review has two columns, so that Pay stays in the first view at 1366 × 768 (Lisa). Under the heading and Back sit two equal columns, gap `{spacing.8}`, each within `{spacing.measure-text}`. The Booking summary is on the left, and the booking terms, Terms checkbox and Pay are on the right. A Notice after a refusal sits above the columns at `{spacing.measure-text}`.

**Administrator pages.** [ASSUMPTION] No rail. The Administrator bar runs full width and content sits under it in one column up to `{spacing.page-max}`, because the booking table needs the width and staff pages have no need for the guest shell. Laptop in Core, mobile later with FR-51.

**Narrow screens.** Breakpoints and collapse order are behaviour and live in `EXPERIENCE.md`, Responsive & Platform. [ASSUMPTION] The side gutter is `{spacing.gutter-narrow}`, taken from the mock's page wrapper. [ASSUMPTION] Type tokens do not change on narrow screens, because no smaller scale was reviewed. The 52 px wordmark has to be checked at 320 px with the real font. No fixed width may block FR-51 (architecture Conventions), so the width tokens above are laptop values and must yield.

## Elevation & Depth

Flat. There are no shadows, no blur and no layering of cards. Depth comes from the small tonal step between `{colors.page}` and `{colors.surface}`, and from thin lines in `{colors.border}`. The only thing that stays above the page is the Fixed action bar on narrow screens, and it is separated by a line, not a shadow. The selected Session row's 3 px bar is a flat inset mark, not elevation.

## Shapes

Square corners everywhere: `{rounded.none}`. Buttons, inputs, calendar days, seat buttons, notices and images all meet the page at a right angle, like a printed leaflet. The only round shapes are the native radio controls in Session rows. The 4 px and 6 px radii in the mock files belong to the mock's browser frames and swatches, not to the product.

No logo, wordmark drawing or icon set exists. The wordmark is typeset text, and the interface uses no icons. State is always said in words.

## Components

Rendered in [`directions-3.html`](mockups/directions-3.html) unless marked. Behaviour for every component is in `EXPERIENCE.md`, Component Patterns, under the same name.

**Shared**

- **Primary button.** `{colors.primary}` fill, `{colors.on-primary}` text, 1.5 px `{colors.button-edge}` edge, `{typography.button}`, at least `{spacing.button-height}` high, `{spacing.5}` side padding, no wrapping. Full width of its column in the rail. One per page. While processing, the fill stays and only the label changes, so it does not read as unavailable.
- **Text link.** `{colors.link}`, underlined always. Never distinguished by colour alone.
- **Wordmark.** "Saunalöyly" set in `{typography.wordmark}` in `{colors.text}`, no underline, at the top of the rail.
- **Rail.** `{colors.page}`, no fill or border of its own, stacked in one column: Wordmark, then the page's facts or total, the action, then notes.
- **Rail note.** `{typography.body-sm}` in `{colors.muted}`, `{spacing.4}` apart.
- **Text field.** Label in `{typography.label}` above, `{spacing.1}` gap. Input `{spacing.control-height}` high, `{colors.surface}`, 1 px `{colors.border}`, square. Hint in `{typography.hint}` and `{colors.muted}` below.
- **Terms checkbox.** Rendered in `mockups/key-review.html`. Native checkbox at 16 px with `{colors.link}` accent, label in `{typography.body-sm}`, matching the radio treatment. The checkbox sits inside its label, so the whole line is the click target. Size and accent follow the radios.
- **Image block.** Fills its container exactly, square corners, no caption and no overlay. Warm, soft light, water in view (PRD §6).

**Book seats**

- **Date calendar.** Text field on top, then a month line in `{typography.small}` with the month name in weight 600 and "Next month" as a Text link, then a seven-column grid with `{spacing.1}` gaps. Bookable day: `{colors.surface}`, 1 px `{colors.border}`, `{spacing.calendar-cell-height}` high. Selected: as Primary button, in `{typography.calendar-day-selected}`. Not bookable: `{colors.unavailable}` fill, `{colors.muted}` number, no border.
- **Seat picker.** Ten equal cells, 1 to 10, `{spacing.1}` gaps, `{spacing.control-height}` high. Selected cell as in the calendar, weight 700.
- **Session list.** Rows stacked with one rule between each and a rule closing the list. No gaps, no cards.
- **Session row.** Three columns: 32 px radio, time in `{typography.session-time}` in a column at least 112 px wide that grows with enlarged text (`minmax(112px, max-content)`, 12 px after the time), then the Seats left text in `{typography.body-sm}`. At least `{spacing.session-row-height}` high, `{spacing.3}` side padding, 1 px `{colors.border}` above. Native radio at 16 px with `{colors.link}` accent. The whole row is the label, so the click target is the full row, at least 40 px high, whatever the radio size. Selected: `{colors.surface}` fill, 3 px inset `{colors.button-edge}` bar on the left, text in weight 600. Unavailable: `{colors.unavailable}` fill, radio disabled, text stays `{colors.text}`.
- **Total block.** Spine name for the rail's total. "Total NOK 500" in `{typography.total}`, "incl. VAT" in `{typography.body-sm}` on the same line, the per-seat line in `{typography.total-note}` and `{colors.muted}` below, `{spacing.3}` above the Primary button.
- **Fixed action bar.** Narrow screens only. Spine only. `{colors.surface}` fill, 1 px `{colors.border}` line on top, `{spacing.3}` padding, holding one full-width Primary button. [ASSUMPTION] Fill and line follow the flat rule above, because this bar has not been rendered.

**Landing**

- **Rule list.** Group title in `{typography.heading-md}`, with a 1 px `{colors.border}` line under it. Items in `{typography.body}` with `{spacing.2}` padding, no lines between them and no bullets (Lisa).
- **Sauna card.** Image `{spacing.sauna-image-height}` high, name in `{typography.heading-lg}` `{spacing.3}` below it, size line in `{colors.muted}`, one line of text in `{typography.body}`. No border, no fill.
- **Find us block.** Heading in `{typography.heading-lg}`, then address and contact, then Text links, all in `{typography.small}`, one column each.

**Messages and confirmation**

Rendered in the key-screen mocks in `mockups/`. Each uses only existing tokens, so no new visual language is introduced.

- **Notice.** `{colors.surface}` fill, 1 px `{colors.border}`, `{spacing.3}` padding, `{typography.body-sm}` in `{colors.text}`. For availability information, including "Sold out". Never `{colors.error}`.
- **Nearest sessions.** Up to three rows inside a Notice, each one Text link with the date, time and Seats left, at least `{spacing.session-row-height}` high, with the Session list's rules between them. No radio and no selected state.
- **Error summary.** `{colors.surface}` fill, 1 px `{colors.error}` line, `{spacing.3}` padding, text in `{colors.error}`, with no title. Each entry with a field is an underlined link in `{colors.error}` to that field, and an entry with no field is plain text.
- **Field error.** Text in `{typography.hint}` and `{colors.error}` directly under the field. The field border does not change colour.
- **Booking summary.** Label and value pairs in `{typography.body}`, with lines in `{colors.border}` between rows.
- **Reference display.** The 8-character Booking reference in `{typography.heading-lg}`, tabular figures, with its label in `{typography.label}` above.
- **Email as sent.** `{colors.surface}` block, 1 px `{colors.border}`, `{spacing.5}` padding, `{typography.small}`, line breaks kept, labelled "Sent by email:" in `{typography.label}`. Plain text, because the emails are plain text.

**Administrator** (Session group and Booking table rendered in [`key-booking-list.html`](mockups/key-booking-list.html), the rest spine only)

- **Administrator bar.** `{colors.bar}` fill, `{colors.on-bar}` text in weight 600, `{spacing.3}` by `{spacing.5}` padding, as the bar in [`color-themes-3.html`](mockups/color-themes-3.html). Name on the left, links on the right.
- **Session group.** Time in `{typography.heading-md}`, figures on one line beside it in `{typography.body-sm}` with tabular figures, rule above. A full Session has a `{colors.unavailable}` header, with its figures in weight 600.
- **Booking table.** Header in `{typography.label}`, rows in `{typography.body-sm}` with 1 px `{colors.border}` lines, numbers right-aligned in tabular figures.
- **Outbox entry.** Same block as Email as sent, with time, recipient and subject above the body in `{typography.label}`.

**If-time plug-ins (spine only, none built in Core)**

- **Private sauna entry.** A Text link. Never a second Primary button.
- **Voucher field.** A Text field with a Text link beside it.
- **Sign-in choice.** One Primary button for continuing without an account, with sign-in as a Text link.
- **Sauna option.** Sauna name in `{typography.heading-md}`, size and price in `{typography.body-sm}`, then Session rows.

## Do's and Don'ts

| Do | Don't |
|---|---|
| One Primary button per page | A second filled button beside it |
| Let photographs carry warmth and the PRD's wood and forest colours | Add wood, green or gradient fills to the interface |
| Say state in words, with colour as support | Icons for state, or colour alone |
| Keep `{colors.error}` for real errors | Show "Sold out" in `{colors.error}` |
| Square corners and thin lines | Rounded cards, pills or shadows |
| Finlandica at 400 and up | Weight 300 in Finlandica, which does not exist and would be faked or substituted |
| Self-host every font and image | Load anything from another origin |
| Warm, softly lit photographs of real saunas and tools | Spa-luxury cues, polished stock photography, heat boasts, sexualised framing (PRD §6) |
| Check Book seats against its first-view budget | Add a banner or a new row without checking the fit at 1366 × 768 |
| Show each fact once on a page (`EXPERIENCE.md`, Content Homes) | Repeat a price, a time or an action to fill space |
