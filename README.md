# flab-DIY-stack

**Build a complete black-and-white film laboratory at home.**

This manual documents practical workflows for modern DIY film development.
It emphasizes phenidone-based chemistry and reusable processes.

The structure is modular. Each component serves a specific function:
- Darkroom construction (safety protocols, chemical storage, organizational systems)
- Negative development (formulations, processing techniques, chemistry maintenance)
- Digitization equipment (technical drawings, parts lists, 3D models, assembly guides)
- **Digital conversion software** (Python tools for patch file processing, target management, and scanning workflows)

These resources target advanced practitioners and experimental photographers.
They combine technical precision with accessible instructions.

> Original content in Russian. English and Polish translations are in progress.
> Software components: English interface, code documentation

---

### Beyond DIY: Lab-Grade Standards

This approach remains accessible but borrows methods from professional environments.
It incorporates structured inventory management with indexed chemical cataloging.
It separates long-term archival storage from daily working solutions.
It employs inert gas preservation techniques to extend chemical life.

These are not amateur improvisations. They are standard practices from photo chemistry and laboratory management.
They transform home setups into precise, reliable workspaces without specialized infrastructure.

Can you implement professional standards in a personal space? Yes. These pages show how.

---

### Why This Project Exists

My former photography students keep asking about analog processes.

Questions accumulated over years: "How do I start?" "What's the proper technique?" "Why did this fail?" "How can I improve?"
These queries formed a pattern. They revealed a need for clear guidance on darkroom setup and workflow organization.

This resource distills practical knowledge for educators and returning enthusiasts.
It aims to replace hours of scattered internet searches with tested, reliable methods.
Safety, accessibility, and educational value guide every recommendation.

These pages contain techniques selected for home labs and classroom settings.
They favor practical solutions over historical completeness or commercial specialization.

This is experience made shareable. Take what serves you. Adapt what doesn't. Pass it forward.

---

## Project Structure

Each language has its own directory: 
`ru/` – Russian (main content) 
`en/`, `pl/` – translations

Inside each language directory, content is structured by modules and stages of the workflow.

**Software tools** are located in the project root:
`tools/` – Python utilities for patch processing and target management

```
├───tools                  / # Python software components
│   └─profiling  
│     ├───PatchReader.py   / # Patch files processing utility 
│     └───...              / # and other tools
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


## License and Attribution

This repository is licensed under [Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

Copyright © 2025 Valdas2000.

You may copy, adapt, translate, and share this material for non-commercial purposes.  
Use in teaching, research, public programs and experimental laboratories is explicitly permitted.  
Attribution is required. The author's name (Valdas2000), a link to this repository, and a note on any changes must be included.  
Reference to the CC BY-NC 4.0 license must be preserved.

Commercial use is not allowed without written permission.  
This includes publication for sale, use in monetized platforms or services, and any derivative work generating revenue.  
To discuss commercial licensing, contact the author at:  
valentin71@gmail.com  
github.com/Valdas2000

It means a great deal to know when this work resonates or proves useful.  
If you include it in a lecture, course, exhibition, article or translation, a short message is welcome.  
This is not required. But this project is alive. I want to know where it travels.
