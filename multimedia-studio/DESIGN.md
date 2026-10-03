# Design System: Multimedia Studio (Saifeddine Fersi)

A one-person motion, 3D and video studio in Schwerin. The site is a portfolio and lead generator: it must show moving work fast and turn visitors into project requests. Language: German first, with English (`/en`) and Arabic (`/ar`, right-to-left) mirrors.

Reference implementation: `index-v2.html`. Copy its `<head>`, `:root` tokens, nav, mobile menu, footer and the shared script helpers (`inView`, `play`, `pause`, `bindVideo`, media skeleton, reveals, magnetic buttons) into every page so all pages behave the same.

**Dials:** Variance 7 (offset, asymmetric where it helps) / Motion 6 (fluid CSS plus a few choreographed loops) / Density 3 (airy gallery).

---

## 1. Visual Theme & Atmosphere

A bright, quiet gallery. The page is a pale slate wall, white cards hang on it with very soft, wide shadows, and the work (looping films, packshots, renders) carries all the colour. One hot orange accent marks every point of action.

Layouts are confident and roomy: big left-aligned statements, generous empty space, media in mixed aspect ratios. Motion is calm and springy. Things slide and settle; nothing blinks or spins for its own sake. A faint film grain sits over everything.

Mood words: bright, precise, tactile, unhurried, crafted.

---

## 2. Colour Palette & Roles

Cool slate/zinc neutrals only. No warm greys or beige.

| Token | Value | Role |
|---|---|---|
| `--bg` | `#F9FAFB` | Page background. Never pure white. |
| `--card` | `#FFFFFF` | Cards, buttons (ghost), the CTA card. |
| `--sunk` | `#F1F2F4` | Media placeholders, tool pills, icon wells, skeletons. |
| `--ink` | `#18181B` | Headlines, primary text, dark bars and badges, service strips. |
| `--ink-2` | `#3F3F46` | Nav links. |
| `--mut` | `#71717A` | Body copy, captions, metadata, footer links (4.6:1 on `--bg`). |
| `--line` | `rgba(203,213,225,.55)` | 1px card edges, nav and footer dividers. |
| `--line-2` | `rgba(148,163,184,.45)` | Slightly stronger dividers in lists (the category hover list). |
| `--acc` | `#FF4D00` | The single accent (see below). |
| `--acc-ink` | `#C23A00` | Orange for **small** text only (labels, "Featured", link hover). 4.9:1. |
| `--on-acc` | `#18181B` | Text and icons on orange fills. |
| `--acc-soft` | `rgba(255,77,0,.09)` | Tinted background behind a highlighted item. |

**Accent rules.** `#FF4D00` is the brand colour and stays fully saturated. Use it for primary button fills, the logo tile, active and hover states, focus rings, check circles and **one emphasised word per headline**. It should cover less than 5% of any screen.
- Orange text in `--acc` is only allowed at headline size (28px and up). Smaller orange text uses `--acc-ink`.
- Labels on orange fills are dark ink (`--on-acc`), never white. White on `#FF4D00` is only 3.4:1 and fails for button text.

**Shadows:** `--shadow: 0 20px 40px -15px rgba(15,23,42,.08)` for resting cards, `--shadow-lg: 0 40px 80px -30px rgba(15,23,42,.18)` for hover and floating elements. Always slate-tinted, never black, never coloured glows (the one exception is a faint orange shadow under a hovered primary button).

**Banned:** purple or blue glows, neon gradients, gradient text, a second accent colour (no green success, no blue links), pure `#000` or `#FFF` text.

---

## 3. Typography

- **One family:** Outfit (Google Fonts, weights 300 to 700) for everything.
- **Headlines:** weight 600, letter-spacing `-.04em` to `-.045em`, line-height 1.02 to 1.05.
  - Hero: `clamp(2.6rem, 4.6vw, 4.4rem)`
  - Section (`.h2`): `clamp(2.2rem, 4vw, 3.75rem)`
  - Max 2 lines on desktop where possible.
- **Emphasised word in a headline:** same family and weight, `font-style:normal`, coloured `--acc` (`<em>` inside `.h2`). Example: "Alles, was dein Projekt **braucht.**"
- **Italic:** used in exactly one place, the second word of each row title in the hover list ("3D *Produkt*"). Outfit has no true italic, and the browser's slanted version looks right at this size, so no serif is loaded. Don't use italic anywhere else.
- **Body:** 400, 16 to 17px, line-height 1.6 to 1.65, `--mut`, max about 56 characters per line (`.lead`).
- **Card titles:** 20px / 600 / `-.02em`. Captions and metadata: 13 to 14px, `--mut`, joined with " · ".
- **Arabic pages:** pair with IBM Plex Sans Arabic at matching weights; mirror the layout with `dir="rtl"`.
- **Banned:** Inter, Roboto, Arial, Helvetica, generic serifs, all-caps paragraphs, small uppercase eyebrows above every heading, numbered section labels.

---

## 4. Shape, Spacing & Layout

- Container `.wrap`: max-width 1400px, side padding 40px (20px below 768px).
- Section spacing `.sec`: 140px top and bottom (104px on phones). Follow-on sections use `padding-top:0` so the gap between sections stays one unit.
- Radii: **2.5rem** (`--R`) for cards, strips and the CTA card; 2rem for project frames; 999px for buttons, chips and pills; 14 to 22px for small tiles.
- Grids always use `minmax(0,1fr)` columns and `min-width:0` children so marquees or long words never widen the page.
- **Card titles and descriptions sit below the card** (`figure` + `figcaption`, or a `.cap` row), never laid over footage. The only text allowed on media is inside the dark service strips, over a bottom gradient.
- Section headers stack: headline, then an optional `.lead` underneath (or headline left and a single button right).
- Never put 3 equal cards in a row. Never use 3 or more image-and-text zigzag rows in a row.
- Below 768px every multi-column layout becomes one column. No horizontal page scroll, ever (marquee tracks are clipped by an `overflow:hidden` parent).
- Full-height sections use `dvh`, never `100vh`.

---

## 5. Components

**Nav (`header.nav`).** Sticky, 72px, `rgba(249,250,251,.82)` with a 16px backdrop blur and a 1px bottom line. Grid `1fr auto 1fr`: logo tile + "Multimedia Studio." left, 4 links centred (Portfolio, Services, Über mich, Kontakt), language switch `DE · EN · AR` plus "Projekt starten" right. Below 960px: logo and a 44px round menu button that opens a full-screen `--bg` panel with 40px stacked links sliding up with a 70ms stagger. Set the current page's link to `aria-current="page"` and give it `color:var(--ink);font-weight:600`.

**Buttons.** Full pills, 15px / 500, min height 44px, padding `6px 6px 6px 24px` with a 38px round icon well on the right (Phosphor `ph-arrow-up-right` for contact, `ph-arrow-right` for internal links).
- `.btn.pri`: orange fill, dark label, icon well `rgba(24,24,27,.1)`, soft orange shadow on hover.
- `.btn.ghost`: white fill, 1px `--line` inset ring, `--shadow`, icon well `--sunk`.
- Hover nudges the icon 2px up-right with a spring. Press scales to .98. `.mag` adds a magnetic pull (mouse only, off with reduced motion).
- One label per intent: "Projekt starten" / "Projekt anfragen" to contact, "Portfolio ansehen" / "Alle ansehen" to the portfolio.

**Project tiles (`.work` in a CSS-columns masonry, `columns:3 320px`).** 1px "spotlight" frame (`.spot`) whose border glows orange under the cursor, white inner plate with 8px padding, media with 1.6rem radius. Hover lifts 4px and scales the clip to 1.04. Title and metadata in a `.cap` row below.

**Bento cards (`figure.bx`).** White `.card`, 320px high, 2.5rem radius, 1px `--line`, `--shadow`, `overflow:hidden`, caption below. Spans on the 10-column grid; 2 columns under 1100px, 1 under 768px.

**Expanding service strips (`.accordion`).** 4 dark (`--ink`) strips, 580px high, 14px gap, 2.5rem radius, each with a looping clip at 35% opacity. Closed: vertical title bottom-left. Hover: `flex` 1 to 3.6 over 1s, clip to full opacity, big two-line title + tag fade up. First strip is open (and playing) when nothing is hovered. Under 900px: stacked 300px cards, always open, clips play when in view.

**Hover list (`.split` + `.cat`).** Left column sticky at `top:120px` (headline with one orange word, `.lead`, ghost button). Right column: rows with number, title (second word italic), tag line and a 48px round arrow. Hover: title slides 14px right, the italic word turns orange, the arrow circle fills orange and rotates 45deg, a 180px tilted preview pops in with a spring. The preview only shows when the list is at least 680px wide (container query), so it never covers the title. Under 960px the columns stack and there is no preview.

**Contact CTA (`.cta`).** Scrolling wall of poster frames (from `assets/work-list.js`) behind a radial `--bg` wash, one white card (2.5rem, `--shadow-lg`) on top with headline, `.lead`, primary + ghost button.

**Footer.** 1px top line, grid `1.6fr 1fr 1fr 1.2fr` (Studio / Services / Info), bottom row with © Impressum · Datenschutz and social links.

**Media states.** Every clip or image sits in a `.media` wrapper:
- Loading: `--sunk` fill with a diagonal shimmer (a translated pseudo-element).
- Failed: the element is hidden and "Vorschau nicht verfügbar" is centred in `--mut`.
- Small media (`.media.sm`: avatars, hover previews): on failure show only the plain grey shape, no message. `img` elements use `color:transparent` so broken-image alt text never shows.
- Images with a second source use `data-fallback="…png"`; the script tries it before marking the media as failed.

**Icons.** Phosphor (web build from unpkg), regular weight, 16 to 20px. Fill/bold variants only for the marquee asterisk and check marks. No emojis.

---

## 6. Motion & Interaction

- Easing: `--ease: cubic-bezier(.16,1,.3,1)` for fades and slides (500 to 1100ms); `--spring: cubic-bezier(.34,1.56,.64,1)` for small elements that should overshoot (icons, badges, previews, list FLIP). Linear only for constant-speed loops (marquee, poster stream, work wall).
- Entry: `.rv` fades up 28px when it enters the viewport; stagger with `style="--i:n"` (80ms steps).
- Animate only `transform` and `opacity`. Documented exceptions: the strips' `flex` change and the 4K frame's `clip-path` morph.
- No scroll listeners. Use `IntersectionObserver` (`inView`) for reveals, video play and every loop. Loops (tools reshuffle, format morph, badge, poster stream, inclusion ticks, scramble line) run only while visible.
- Video: muted, looped, `playsinline`. Hero clip autoplays. Everything else plays on hover where the device has a real mouse (`(hover:hover) and (pointer:fine)`) and plays when in view otherwise.
- `prefers-reduced-motion`: reveals appear instantly, all loops stop, videos never start on their own, typewriter and scramble stay on their first word.
- Blur only on the sticky nav and small glass chips. Grain is a fixed `pointer-events:none` overlay.

---

## 7. Responsive Rules

- Breakpoints: 1100px (bento to 2 columns, work wall to 6 columns), 960px (mobile nav, hover list stacks), 900px (hero stacks, strips stack), 767px (single column everywhere, 20px gutters).
- Tap targets at least 44 by 44px. Body text never below 16px in paragraphs.
- Hover-only behaviours switch to "always open" or "play when in view" on touch.
- Arabic pages mirror every asymmetric layout.

---

## 8. Content Rules

- Real content only: the actual project names (3D Headset, Cosmetic Product, Character Animation, Weekend Parfum, Keyboard, Koffee, Qahwa, ELFER, Norée …), real tools (Blender, After Effects, Illustrator, DaVinci Resolve, InDesign, Premiere Pro) and real figures (10+ Jahre, 120+ Projekte, 4 Sprachen).
- No invented testimonials, client logos or metrics. No AI clichés ("Elevate", "Seamless", "Unleash").
- Tone: direct, first person, concrete ("Du arbeitest direkt mit mir."). Short sentences. **No em-dashes** in visible text; use commas, colons or periods.
- Imagery: always the studio's own renders and poster frames, from `assets/videos/web/` and `assets/posters/`.

---

## 9. Building another page

1. Start from `index-v2.html`: keep `<head>`, tokens, nav (mark the current link), mobile menu, footer, `assets/work-list.js` and the shared script helpers.
2. Open with a left-aligned hero or page header: `.h2`/`h1` with one orange word, a `.lead`, at most one primary and one ghost button. No centred hero.
3. Pick a different layout family for each section from: masonry, expanding strips, hover list, bento, swipe stack, statement line, CTA over the work wall.
4. End with the CTA section and footer.
5. Check at 1440px and 390px: no horizontal scroll, no console errors, all media states work.
