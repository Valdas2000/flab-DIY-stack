# flab-DIY-stack

**An open-source technical manual and toolkit for building a black-and-white film lab at home.**

This project documents the practical and chemical workflows behind DIY film development using 
modern materials and techniques, with a special focus on phenidone-based developers.

It is built as a modular knowledge stack for advanced hobbyists and analog photographers, 
providing end-to-end instructions, printable resources, 3D-printable lab components, 
and calibration workflows.

The project covers all aspects of black-and-white film processing — from in-house darkroom 
setup (safety, chemical storage, labeling systems), through negative 
development (recipes, technologies, reusable chemistry), to digitizing 
equipment (drawings, estimates, 3D models, wiring, assembly), and finally to positive 
processing (digitization and tonal inversion).


>The original content is written in Russian, with planned translations into English and Polish.

---

## Project Structure

Each language has its own directory: 
`ru/` – Russian (main content) 
`en/`, `pl/` – translations

Inside each language directory, content is structured by modules and stages of the workflow.
```

├───1_10_Intro             / # Introduction and philosophy
├───1_20_Home_Lab          / # Basic lab setup, safety
├───1_30_Chemistry_Storage / # Chemical storage, labeling, CO₂ prep
│   ├───img                / # Inline illustrations
│   └───pdf_stickers       / # Printable stickers for chemical jars
├───2_10_NegativeProcess   / # Film development overview
├───2_20_Recipies          / # Step-by-step development process
│   └───pdf_cards          / # Reference cards and printables
├───3_10_Equipment         / # Common tools
│   └───img
├───3_20_Agitator          / # Horizontal agitation unit (DIY)
│   ├───img
│   ├───pdf_drawings
│   └───stl_3d_models
├───3_30_DigitazingStand   / # Repro stand for scanning negatives
│   ├───img
│   ├───pdf_drawings
│   └───stl_3d_models
├───4_10_ReversalProcess   / # Reversal processing
├───4_20_BW_profiling      / # Create a profile for Reversal processing for B&W
├───4_30_COLOR_profiling   / # Create a profile for Reversal processing for Color films
├───4_40_Profile_usage     / # Profile-based Reversal processing
└───4_50_LUT_usage         / # LUT-bases Reversal processing
```

---

## Naming Conventions

- All folder names begin with a two-digit prefix to preserve order (`1_10`, `2_20`, etc.)
- Subfolders such as `img/`, `pdf_cards/`, and `stl_3d_models/` 
contain **media tightly coupled with the main content** in that module.
- Only specific file formats are allowed per subfolder (enforced via `.gitignore`):
  - `img/` → `.jpg`, `.png`, `.webp`
  - `pdf_cards/`, `pdf_stickers/`, `pdf_drawings/` → `.pdf`
  - `stl_3d_models/` → `.stl`


## License

All content in this repository is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). 
Copyright © 2025 Valdas2000.

You are free to share and adapt this work, including for commercial purposes, with proper attribution.

