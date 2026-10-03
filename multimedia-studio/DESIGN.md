# Design System: Multimedia Studio (Saifeddine Fersi)

A one-person motion, 3D and video studio in Schwerin. The site is a portfolio and lead generator: it must show moving work fast and turn visitors into project requests. Language: German first, with English (`/en`) and Arabic (`/ar`, right-to-left) mirrors.

**Dials:** Variance 8 ("Offset Asymmetric", leaning artsy) / Motion 6 ("Fluid CSS", with a few choreographed moments) / Density 3 ("Art Gallery Airy").

---

## 1. Visual Theme & Atmosphere

A dark, cinematic screening room. The interface is a quiet charcoal stage, and the work is the only thing lit. Surfaces recede; the looping product films, packshots and character renders carry all the color. One hot ember accent marks every point of action, the way a single tally light marks the live camera.

Layouts are confident and offset: big left-aligned statements, generous empty space, media of varying aspect ratios that never line up into a predictable grid. Motion is weighty and calm. Things slide and settle with spring physics; nothing bounces, blinks or spins for its own sake. A faint film grain sits over everything, so the page feels photographed rather than rendered.

Mood words: nocturnal, precise, tactile, unhurried, crafted.

---

## 2. Color Palette & Roles

One palette, cool zinc neutrals only. Never mix in warm greys or beige.

- **Stage Charcoal** (#0C0C0E) - Page background. The darkened screening room. Never pure black.
- **Panel Zinc** (#151518) - Cards, media frames, menus and the contact panel.
- **Raised Zinc** (#1D1D21) - Hover fills, tool pills, input backgrounds, skeleton loaders.
- **Projector White** (#EDEDEB) - Headlines and primary text. Off-white, never #FFFFFF.
- **Muted Steel** (#9A9AA2) - Body copy, captions, project metadata, footer links.
- **Dim Steel** (#5E5E66) - Disabled states and inactive marquee words.
- **Hairline** (rgba(237,237,235,0.08)) - 1px structural lines and card edges.
- **Ember Signal** (#FF4D00) - The single accent: primary CTA fill, the logo tile, active states, focus rings, one emphasized word per headline. Text on Ember is Stage Charcoal (#0C0C0E) for contrast.

**Accent exception, documented on purpose:** Ember Signal is the studio's existing brand color and is fully saturated. It breaks the usual "under 80% saturation" rule; that is accepted only for brand fidelity. Compensate by using it sparingly. It should cover less than 5% of any screen.

**Banned:** purple or blue glows, neon gradients, gradient text on headlines, a second accent color anywhere (no green success badges, no blue links), pure #000000 or #FFFFFF.

---

## 3. Typography Rules

- **Display:** Satoshi, Bold (700) and Medium (500). Tight tracking (-0.035em), compressed leading (1.0 to 1.05). Hierarchy comes from weight and color, not raw size. Headlines max 2 lines on desktop. Scale with `clamp(2.5rem, 5vw, 4.75rem)` for the hero and `clamp(2rem, 4vw, 3.75rem)` for section headlines.
- **Emphasis inside a headline:** the same family in Bold, colored Ember Signal (for example "Motion Design, 3D und Video **aus einer Hand.**"). Never switch to a serif for the emphasized word.
- **Body:** Satoshi Regular (400), 16 to 18px, line-height 1.65, Muted Steel, max 60 characters per line.
- **Mono:** JetBrains Mono, 12 to 13px, tracking 0.04em. Only for project metadata (tool, discipline, year), timecodes and stat captions. Never for paragraphs.
- **Arabic pages:** pair with IBM Plex Sans Arabic at matching weights; mirror the layout with `dir="rtl"`.
- **Banned:** Inter, Roboto, Arial, Helvetica, any generic serif (Times, Georgia, Garamond). No all-caps paragraphs. No headline wider than 2 lines on desktop.

---

## 4. Hero Section

- **Structure:** asymmetric and left-aligned. The headline spans the top; below it sits a split with a short supporting line plus one CTA on the left (4 of 12 columns) and a wide looping hero film on the right (8 of 12 columns, 16:9, Panel Zinc frame).
- **Signature move, inline image typography:** small rounded clips of real renders (headset, perfume bottle, coffee pack, character) sit between words of the headline at cap height, about 1.8em wide and 0.8em tall, fully rounded. They act as visual punctuation. On mobile they drop below the headline as a horizontal row.
- **Copy:** headline max 8 words, supporting line max 20 words.
- **CTA restraint:** exactly one primary CTA, "Projekt starten". No secondary button in the hero.
- **No overlap:** text never sits on top of media. Every element owns its own zone.
- **Banned:** centered hero, stats or trust strips inside the hero, location eyebrows, "Scroll", bouncing chevrons, mouse-wheel icons.

---

## 5. Component Stylings

- **Primary button:** a full pill. Ember Signal fill, Stage Charcoal label, 14px vertical and 24px horizontal padding. A trailing arrow icon (Phosphor Light, `arrow-up-right`) nudges 3px up and right on hover. On press the whole button scales to 0.98. No glow; at most a soft, ember-tinted shadow on hover.
- **Secondary button:** a full pill with a Hairline outline and Projector White label. Hover fills it Projector White with a Stage Charcoal label. Only outside the hero.
- **One label per intent across the whole site:** "Projekt starten" for anything that leads to contact, "Portfolio ansehen" for anything that leads to the portfolio.
- **Media cards (project tiles):** 16px corner radius, Panel Zinc fill, no border. The video fills the card and plays on hover (in view on touch). On hover the clip scales to 1.04 over 1s. Title and metadata sit *below* the media, never as pills or labels on top of the footage.
- **Content cards (bento tiles):** 16px radius, Panel Zinc, a 1px inner highlight at the top edge (rgba(255,255,255,0.06)). Shadows only when elevation means something, always tinted dark zinc (`0 30px 60px -30px rgba(0,0,0,0.8)`).
- **Expanding service strips:** a row of 4 tall media strips (600px high, 12px gap). Closed strips show their title written vertically at the bottom-left. Hovering a strip widens it to about 3.5 times the others, brings its video to full opacity, and fades up a large two-line title plus a mono tag line. The first strip is open when nothing is hovered. On mobile they become stacked 300px cards, always open, with no vertical text.
- **Inputs (contact form):** label above in Projector White, field in Raised Zinc with a Hairline edge and 12px radius, helper text below in Muted Steel, error text below in Ember Signal. Focus ring: 2px Ember Signal. No floating labels; no placeholder used as a label.
- **Loaders:** a skeleton block with the exact aspect ratio of the media it replaces, in Raised Zinc with a slow diagonal shimmer. No circular spinners.
- **Error state for media:** if a clip fails, the frame stays and shows "Vorschau nicht verfügbar" centered in Muted Steel.
- **Empty states:** for example a portfolio filter with no results. Show one muted poster frame, a one-line message, and a "Filter zurücksetzen" pill.
- **Icons:** Phosphor Light only, 1.5px stroke, sized 16 to 20px. No emojis anywhere.

---

## 6. Layout Principles

- 12-column CSS Grid, max-width 1360px, 40px side padding (20px on mobile).
- Section spacing `clamp(6rem, 12vw, 10rem)` vertically. Sections should feel like separate scenes.
- Each section uses a different layout family. Approved families for this site:
  1. Asymmetric hero split with inline image typography.
  2. A single kinetic statement line ("Ich gestalte ..." with a rotating word in Ember Signal).
  3. Project gallery as an offset two-column masonry (right column starts lower), or as a horizontal scroll-snap rail with arrow controls.
  4. Expanding service strips.
  5. Asymmetric bento with exactly 5 cells for the 5 promises (Ultra-HD video, 4K, tools, personal with stats, all-inclusive price). Desktop spans 8+4 / 4+5+3. At least 3 cells carry real visual variation (video, portrait, Ember fill).
  6. Fanned packshot stack (4 portrait clips rotated -21, -7, 7 and 21 degrees, spreading on hover).
  7. Full-bleed contact scene: the scrolling wall of poster frames, darkened, with one solid Panel Zinc card on top.
- Never use 3 equal cards in a row. Never use 3 or more consecutive image-and-text zigzag rows.
- Section headers stack vertically: headline, then an optional short paragraph underneath. No small explainer floating in the top-right corner.
- Full-height sections use `min-height: 100dvh`, never `100vh`.
- No absolute-positioned text stacked over other content. Overlays on media are limited to a bottom gradient behind a title.

---

## 7. Responsive Rules

- Below 768px every multi-column layout collapses to a single column. No horizontal page scroll, ever (the only sideways movement allowed is a deliberate scroll-snap rail).
- Headlines scale with `clamp()`. Body text never below 16px.
- Every tap target at least 44 by 44px.
- Desktop nav (logo, 4 links, language switch DE / EN / AR, one CTA, all on one line, 68px high) becomes a logo plus a menu button. The menu opens a full-screen Stage Charcoal panel with large stacked links that slide up in a staggered cascade.
- Hover-only behaviors (video on hover, expanding strips, fan spread) switch to "play when in view" and "always open" on touch devices.
- Arabic pages mirror all asymmetric layouts.

---

## 8. Motion & Interaction

- **Physics:** spring feel for interactive elements (stiffness 100, damping 20). For CSS, use `cubic-bezier(0.16, 1, 0.3, 1)` at 500 to 900ms. No linear easing, except for constant-speed loops (the marquee and the poster wall).
- **Entry:** sections fade up 24px into place as they enter the viewport (IntersectionObserver). Lists and grids cascade with a 60 to 80ms stagger.
- **Perpetual micro-loops, used only where they mean something:**
  - One services marquee (the only marquee on the page).
  - The rotating word in the statement line.
  - The slowly scrolling poster wall behind the contact card.
  - A gentle shimmer on loading skeletons.
- **Video:** clips are muted, looped and inline. Hero clip autoplays. All others play on hover (desktop) or when in view (touch) and pause when they leave.
- **Performance:** animate only `transform` and `opacity`. Grain lives on a fixed, pointer-events-none overlay. Blur is only allowed on the fixed nav. No scroll event listeners; use IntersectionObserver or CSS scroll-driven animations.
- **Reduced motion:** with `prefers-reduced-motion`, all loops stop, reveals appear instantly and videos do not autoplay.

---

## 9. Content Rules

- Real content only: the actual project names (3D Headset, Cosmetic Product, Character Animation, Weekend Parfum, Keyboard, Koffee), real tools (Blender, After Effects, Illustrator, DaVinci Resolve, InDesign, Premiere Pro) and real figures (10+ Jahre, 120+ Projekte, 4 Sprachen).
- No invented testimonials, client logos or metrics.
- Copy tone: direct, first person, concrete ("Du arbeitest direkt mit mir."). Short sentences, periods and commas. No em-dashes.
- Imagery: always the studio's own renders and poster frames. Never stock photography.

---

## 10. Anti-Patterns (Never Do)

- No emojis.
- No Inter, Roboto, Arial or generic serif fonts.
- No pure black (#000000) or pure white (#FFFFFF).
- No neon or outer-glow shadows, no purple/blue AI gradients, no gradient text.
- No second accent color.
- No custom mouse cursors.
- No overlapping text and media; no pills or labels laid over footage.
- No 3 equal cards in a row.
- No centered hero.
- No more than one CTA in the hero; no two different labels for the same action.
- No "Scroll to explore", scroll arrows, bouncing chevrons or mouse-wheel icons.
- No small uppercase eyebrow above every heading, no numbered section labels ("01 / Services").
- No generic names or invented brands (John Doe, Acme, Nexus).
- No fake round numbers (99.99%, 50%) or invented stats.
- No AI copywriting clichés ("Elevate", "Seamless", "Unleash", "Next-Gen").
- No broken image links. If a placeholder is unavoidable, use `https://picsum.photos/seed/{project}/{w}/{h}`.
- No `100vh` full-height sections, no horizontal page scroll on mobile.
