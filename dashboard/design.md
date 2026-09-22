# Pairo Landing Page — Design Specification

## 1. Direction générale

Style:

- Dark futuristic SaaS
- Premium, minimal, slightly playful
- Visual focus on central mascot
- Floating product UI cards around mascot
- Subtle orange glow
- Very dark navy/black background

Reference viewport:

- Desktop: 1680 × 900
- Content max-width: 1320px

---

## 2. Colors

Background:

- Main: #08090D
- Secondary: #0D0F15

Text:

- Primary: #F5F7FA
- Secondary: #A6ABB5
- Muted: #6C7280

Accent:

- Orange: #FF7A32
- Orange light: #FF9A59
- Orange glow: rgba(255, 122, 50, 0.25)

Success:

- #38D996

Danger:

- #FF5D61

Borders:

- rgba(255,255,255,0.08)

---

## 3. Typography

Font:

- Geist / Inter / Satoshi

Hero title:

- 72px desktop
- 64px laptop
- 44px mobile
- font-weight: 700
- line-height: 0.98
- letter-spacing: -0.04em

Body:

- 18px
- line-height: 1.6
- color: secondary

Navbar:

- 14px
- medium weight

---

## 4. Navbar

Height:

- 84px

Layout:

- Logo left
- Nav centered
- Sign in + primary CTA right

CTA:

- Orange gradient
- 12px vertical padding
- 22px horizontal padding
- border-radius: 14px

---

## 5. Hero

Height:

- ~760px desktop

Hero centered horizontally.

Structure:

[small trust badge]

AI code reviews
that actually help

Subtitle

[Get started free] [See how it works]

Mascot below CTAs

Floating UI cards positioned around mascot

---

## 6. Hero headline

Maximum width:

- 760px

First line:

- white

Second line:

- orange gradient

Gradient:
linear-gradient(
90deg,
#FF873D,
#FFA060
)

---

## 7. Mascot

Position:

- absolute/relative center
- below CTA area
- width: 350–420px

Desktop position:

- center X
- top around 370px

Effects:

- soft orange backlight
- subtle drop shadow
- faint orbit line behind character

Animation:

- float vertically 8–12px
- duration 4–5s
- ease-in-out
- slight rotation ±1.5deg

Do NOT overanimate.

---

## 8. Floating cards

General style:

background:
rgba(15, 17, 24, 0.9)

border:
1px solid rgba(255,255,255,0.08)

border-radius:
20px

box-shadow:
0 20px 80px rgba(0,0,0,0.4)

backdrop-filter:
blur(16px)

Cards should be slightly rotated.

### Left top card

Pull Request Review

Position:

- left: 8%
- top: 180px

Width:

- 330px

Rotate:

- -4deg

### Left bottom card

AI Suggestion

Position:

- left: 6%
- top: 520px

Width:

- 390px

Rotate:

- -1deg

### Right top card

Security Alert

Position:

- right: 6%
- top: 180px

Width:

- 350px

Rotate:

- 4deg

### Right bottom card

Impact analytics

Position:

- right: 9%
- top: 500px

Width:

- 360px

---

## 9. Background

Dark background with faint grid.

Grid:

- opacity: 0.07
- size: 64px × 64px

Optional radial glow:

radial-gradient(
circle at 50% 55%,
rgba(255,122,50,0.13),
transparent 35%
)

Bottom:

- curved dark planet/horizon effect
- very subtle blue rim light

---

## 10. Buttons

Primary:

background:
linear-gradient(
180deg,
#FF984F,
#FF7528
)

border-radius:
14px

height:
48px

box-shadow:
0 8px 30px rgba(255,122,50,0.25)

Secondary:

background:
rgba(255,255,255,0.03)

border:
1px solid rgba(255,255,255,0.12)

---

## 11. Motion

Use Framer Motion.

Hero cards:

- enter from y: 20
- opacity: 0 → 1
- stagger: 0.1s

Mascot:

- continuous subtle floating

Cards on hover:

- translateY(-4px)
- slightly reduce rotation
- shadow stronger

Do not use aggressive parallax.

---

## 12. Responsive

Below 1100px:

- Reduce floating card size
- Move cards closer to center

Below 768px:

- Hide 2–3 floating cards
- Mascot width: 280px
- Hero title: 44px
- Cards become stacked below mascot
- Remove strong rotations

Mobile order:

Headline
Subtitle
CTA
Mascot
PR card
Security card
Impact card
