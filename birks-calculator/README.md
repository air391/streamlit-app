# Birks' Law Calculator

A Streamlit application for calculating the quenching effect in scintillator materials using Birks' Law and SRIM stopping power data.

## Overview

This application helps physicists and researchers analyze the non-linear light response of scintillators to ionizing particles. It uses SRIM (Stopping and Range of Ions in Matter) stopping power data to calculate visible energy output considering Birks' quenching effect.

## Features

- **Data Input Options:**
  - Load pre-configured datasets (Alpha in GAGG, Proton in NaI)
  - Upload custom SRIM output files

- **Forward Calculation:**
  - Input: Particle energy + Birks constant
  - Output: Visible energy (light output) and quenching factor

- **Inverse Solver:**
  - Input: Particle energy + Observed light output
  - Output: Calculated Birks constant

- **Visualization:**
  - Interactive plots of stopping power vs energy
  - Real-time calculation results

## Installation

```bash
# Install dependencies (from repository root)
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
cd birks-calculator
streamlit run app.py
```

## File Structure

```
birks-calculator/
├── app.py              # Main Streamlit application
├── srim_parser.py      # SRIM file parsing utilities
├── physics.py          # Physics calculations (Birks' Law)
├── presets.json        # Pre-loaded SRIM datasets
└── README.md           # This file
```

## Physics Background

### Birks' Law

Birks' Law describes the saturation of light output in scintillators:

```
dL/dx = S * (dE/dx) / (1 + kB * dE/dx)
```

Where:
- `dL/dx`: Light yield per unit path length
- `dE/dx`: Energy loss per unit path length (stopping power)
- `kB`: Birks constant (material-dependent)
- `S`: Scintillation efficiency

### Visible Energy Calculation

The total visible energy is calculated by integrating:

```
E_visible = ∫[0 to E_init] dE / (1 + kB * dE/dx(E))
```

## SRIM File Format

The application can parse standard SRIM output files. The parser automatically:
- Handles mixed units (eV, keV, MeV, GeV)
- Extracts Energy and Electronic Stopping columns
- Converts all values to consistent units (MeV)

## Typical Birks Constants

- **Organic scintillators:** 10-20 µm/MeV (0.01-0.02 mm/MeV)
- **Inorganic scintillators:** 5-15 µm/MeV (0.005-0.015 mm/MeV)
- **GAGG (Gd₃Al₂Ga₃O₁₂):** ~10 µm/MeV
- **NaI(Tl):** ~12 µm/MeV

## References

1. Birks, J. B. (1964). *The Theory and Practice of Scintillation Counting*
2. Ziegler, J. F. *SRIM - The Stopping and Range of Ions in Matter*. [www.srim.org](http://www.srim.org)
3. Vasil'ev, Y. A. (2008). *Application of Birks' formula to scintillator non-linearity*

## License

This project shares the license of the parent repository.
