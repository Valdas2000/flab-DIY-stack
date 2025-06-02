# flab-DIY-stack

**An open-source technical manual and toolkit for building a black-and-white film lab at home.**

This project documents the practical and chemical workflows behind DIY film development using 
modern materials and techniques, with a special focus on phenidone-based developers.

It is built as a modular knowledge stack for advanced hobbyists and analog photographers, 
providing end-to-end instructions, printable resources, 3D-printable lab components, and calibration workflows.

The project covers all aspects of black-and-white film processing — from in-house darkroom setup (safety, 
chemical storage, labeling systems), through negative development (recipes, processing techniques, 
reusable chemistry), to digitizing equipment (drawings, estimates, STL models, wiring, assembly), 
and finally to positive processing (digitization and tonal inversion).

> The original content is written in Russian, with planned translations into English and Polish.

---

### Semi-Professional DIY Approach

While this project is DIY-oriented, the organization and methodology align more closely 
with those of a small professional lab. It features structured inventory management (including 
internal indexing and cataloging of substances), best practices for storage (separating long-term 
archival and short-term operational chemicals), and encapsulated preservation methods using inert gases. 
These techniques elevate a home lab setup to a semi-professional standard, borrowing from the modern 
practices of photo chemists and general laboratory technicians.

Yes — it can be done at home, and these are the best practices known to contemporary analog workflow specialists.

---

### Educational Background and Motivation

This open-source project is partly a response to questions from my former students who are asking me about analog photography.

Over the years, I've collected and systematized answers to questions ranging from "Where do I begin?" 
and "How do I do this properly?" to "What went wrong?" and "How can I improve this setup?". 
These questions, and the desire to provide structured, reliable guidance, gave rise to this modular 
resource covering lab construction and process organization.

I hope that fellow educators and enthusiasts returning to analog photography will find this material 
helpful—not only to reduce the time spent searching through scattered online sources, but also to provide 
a solid and safe starting point for their creative journeys.

This project reflects my ongoing effort to select the best available methods, tools, and workflows 
that are practical, safe, and educationally appropriate for home and classroom use. 

I'm happy to share my experience—feel free to build upon it, remix it, and make it your own.


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
├───3_30_DigitizingStand   / # Repro stand for scanning negatives
│   ├───img
│   ├───pdf_drawings
│   └───stl_3d_models
├───4_10_ReversalProcess   / # Reversal processing
├───4_20_BW_profiling      / # Create a profile for Reversal processing for B&W
├───4_30_COLOR_profiling   / # Create a profile for Reversal processing for Color films
├───4_40_Profile_usage     / # Profile-based Reversal processing
└───4_50_LUT_usage         / # LUT-based Reversal processing
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

