# Profiling Toolkit for Film Reversal and Digitisation

## Development Notice

This toolkit is currently in development. The GUI and core algorithms are  
functional, but colour profile generation is not yet implemented. This version  
demonstrates the intended workflow and serves as a foundation for the complete  
system.


## Overview

This tool is a practical demonstrator designed to support a wide range of film
digitisation workflows. It is part of a larger educational project and includes
a user-friendly GUI, detailed documentation, and ready-to-use configuration
environments (via `venv` and `uv`).

Rather than replicating existing commercial profiling suites, this toolkit
focuses on accessibility, clarity, and practical value. It enables users to
generate colour-managed outputs from film or test charts — even without access
to spectrophotometers or high-end cameras.

## What It Does

- **Target Generation**  
  Creates grayscale and colour targets optimised for tone and gamut mapping.  
  Includes presets (e.g. 255-patch A6, 720-patch A4), and automatic patch  
  filtering to reduce redundancy.

- **Exposure Selection via Bracketing**  
  Selects the best exposure from a bracketed series, based on detail retention  
  rather than aesthetics. Works with film negatives or printed targets.

- **Lighting-Aware Profiling**  
  Supports profiles adapted to various illuminants (e.g. 3000K, 5000K), with  
  interpolation between them. Generates ICC profiles, DNG Camera Profiles,  
  and LUTs — suitable for use in both RAW and colour-managed pipelines.

- **Software Compatibility**  
  Output profiles can be used directly in:  
  Capture One, Lightroom, Adobe Camera Raw, darktable, RawTherapee, ON1,  
  DxO PhotoLab, Affinity Photo, and any other software supporting ICC/DCP/LUT  
  colour management.  
  Full integration with ArgyllCMS allows for custom workflows and softproofing.

- **Fallback Modes**  
  If no spectrophotometer or IT8 target is available, the system can still  
  match to a reference TIFF or analyse statistical similarity to calibrate output.

## Dual Purpose: Tool and Learning Platform

This toolkit is designed not only as a working solution for digitisation and
profiling workflows — but also as a transparent, hands-on learning platform.

- **For practitioners**: It automates repetitive profiling and reversal tasks,  
  adapts to available equipment, and generates useful outputs even without  
  high-end gear.

- **For learners**: It reveals the internal logic of digital colour workflows —  
  including exposure tuning, patch analysis, colour difference (ΔE), and LUT  
  construction. Users can observe, experiment, and improve their understanding.

You can use it in 'set-and-go' mode — or explore the underlying mechanisms,  
study the generated profiles, and build your own insights.

The included documentation is structured to support both routes:  
a quick-start track for getting results, and a detailed track for learning.

## Use Cases

- **Archival Digitisation** — for museums and institutions preserving analogue  
  material (even nitrate-based stock).
- **Creative Reversal Profiles** — for simulating specific film looks or reversal  
  pipelines.
- **Fine Art Copywork** — when precise tone and gamut reproduction are essential.
- **Educational Projects** — as a learning tool for colour science and analogue  
  imaging.

## Requirements

- **Camera**: DSLR or mirrorless, full-frame or crop, with RAW output.
- **Lens**: Macro (1:1 recommended) or standard lens.
- **Lighting**: High-CRI LED light source (Ra ≥ 95, low R9 drift).
- **Optional**: Spectrophotometer, grey card, IT8 target.
- **Software**: Python 3.13+, ArgyllCMS.

DIY digitising stands and light adapters are documented in the guide.

## Quality Metrics (Defaults)

- **Digital Captures**:  
  ΔE ≤ 2.0 — Excellent  
  ΔE ≤ 3.0 — Acceptable  
  ΔE > 5.0 — Review capture or lighting

- **Film Negatives**:  
  ΔE ≤ 4.0 — Excellent  
  ΔE ≤ 7.0 — Typical  
  ΔE > 12 — Likely exposure misalignment

All metrics can be customised. Colour temperature drift (±15K) and CRI R9  
performance should be monitored.

## Documentation

Comprehensive, readable documentation is in active development. It includes:

- Practical examples and visual references  
- Explanations of key terms (ΔE, tone mapping, LUTs)  
- Workflows for both hobbyists and professionals  
- Tips for integrating results with common photo editing software

## Final Notes

This is not only a general-purpose scanning tool. It is a targeted solution for
those who want to understand and manage the colour flow from analogue to
digital — whether for preservation, study, or creative control.
