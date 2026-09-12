---
version: 1
name: "QR Studio"
description: "A precise optical workbench for generating transparent, logo-bearing QR codes."
colors:
  ink: "#1D1F2A"
  muted: "#1B365D"
  canvas: "#F1F0EC"
  surface: "#FFFFFF"
  line: "#BBBCBC"
  primary: "#004C97"
  pale: "#D5EBEE"
  signal: "#3DCBD9"
  accent: "#A4DBE8"
  danger: "#E4002B"
typography:
  sans:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
  mono:
    fontFamily: "'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
rounded:
  DEFAULT: "0.75rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1.5rem"
spacing:
  section-gap: "2rem"
  page-max: "76rem"
components:
  button: {}
  card: {}
  input: {}
---

# QR Studio Design System

## Overview

The interface borrows from an optical calibration bench: precise registration marks, measured spacing, and a live specimen under inspection. It is a single-page Chinese-language product tool for people generating downloadable QR artwork on desktop or mobile. The checkerboard preview and one scanning light band are its signature; controls remain quiet and familiar. `DESIGN.md` owns the tokens, mirrored one-to-one by CSS custom properties in `web_app.py`.

## Colors and typography

The supplied Pantone palette is the sole color source. Cloud Dancer frames the page; white holds working surfaces; 9460 C and 635 C build the transparent preview grid. Pantone 2945 C identifies primary actions, 534 C carries secondary text, and 532 C provides QR-like contrast. The supplied cyan is reserved for the scanning signal and red only for actionable errors. The UI uses local system sans fonts to avoid network loading and a local monospace stack for measurements.

## Layout and shapes

The desktop canvas is a two-column workbench with a narrower control rail and a square preview stage; it collapses to one column below 820px. Spacing follows a compact 4/8/12/16/24/32 rhythm. Inputs and buttons use 12px corners, panels use 24px corners, and QR artwork remains geometrically square.

## Components and behavior

Inputs have persistent labels and help/error text. The QR color field accepts only `#RRGGBB`, mirrors valid input in a visible swatch, and applies one color consistently to modules, frame, and logo. Output format uses a two-option native radio group: SVG remains editable vector artwork while PNG is a transparent raster export. The form owns validation, disables duplicate submission, and keeps button geometry fixed while busy. Status uses an accessible live region. The download action only appears after a successful generation. All enabled actions have hover, pressed, and visible focus states; disabled states are non-interactive. Global scrollbars use the documented tokens. Motion communicates generation only and is disabled under reduced-motion preferences.

## Do's and Don'ts

- **Do:** Show transparency explicitly with a checkerboard stage.
- **Do:** Keep measurements and generated metadata compact and scannable.
- **Don't:** Add ornamental gradients, floating cards, or framework dependencies.
- **Don't:** hide errors in transient notifications or rely on color alone.
