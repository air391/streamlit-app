"""
SRIM Parser Module
Parses raw SRIM output text files and extracts Energy and dE/dx data.
"""

import re
import pandas as pd
import numpy as np


def parse_srim_text(content: str) -> pd.DataFrame:
    """
    Parse raw SRIM output text and extract Energy and dE/dx (Electronic) data.
    
    Parameters
    ----------
    content : str
        Raw string content from SRIM output file
        
    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['Energy_MeV', 'dE_dx'] where:
        - Energy_MeV: Ion energy in MeV
        - dE_dx: Electronic stopping power (typically in MeV/mm or similar units)
    
    Notes
    -----
    - Handles mixed units (eV, keV, MeV, GeV) and converts all to MeV
    - Skips header and footer lines
    - Robust to variable whitespace in SRIM output
    """
    lines = content.strip().split('\n')
    
    # Find the data section
    # Strategy: Look for lines matching energy pattern, collect all such consecutive lines
    data_start_idx = None
    data_end_idx = None
    
    # First, try to find column headers
    for i, line in enumerate(lines):
        # Look for column headers containing "Energy" and "Elec"
        if 'Energy' in line and ('Elec' in line or 'Electronic' in line):
            # Skip the header and the separator line (dashes)
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith('-') or lines[j].strip().startswith('='):
                    data_start_idx = j + 1
                    break
            if data_start_idx is None:
                data_start_idx = i + 1
            break
    
    # If we found headers, find where data ends
    if data_start_idx is not None:
        for i in range(data_start_idx, len(lines)):
            stripped = lines[i].strip()
            # Data section ends with separators, empty lines, or specific keywords
            # But not if it's at the start (we just skipped those)
            if (not stripped or 
                (stripped.startswith('---') and i > data_start_idx) or
                (stripped.startswith('===') and i > data_start_idx) or
                stripped.startswith('Multiply') or
                'Stopping' in stripped and 'Units' in stripped):
                data_end_idx = i
                break
    
    # If we didn't find clear markers, look for data lines directly
    if data_start_idx is None:
        energy_pattern = re.compile(r'^\s*[\d.]+\s*[kMGTe]?eV')
        for i, line in enumerate(lines):
            if energy_pattern.match(line):
                if data_start_idx is None:
                    data_start_idx = i
            elif data_start_idx is not None and line.strip() and not energy_pattern.match(line):
                # Found first non-data line after data started
                if not line.strip().startswith(('-', '=')):
                    continue
                data_end_idx = i
                break
    
    if data_start_idx is None:
        raise ValueError("Could not find data section in SRIM output. "
                        "Please ensure the file contains energy data with units (keV, MeV, etc.).")
    
    # If no end found, use all remaining lines
    if data_end_idx is None:
        data_end_idx = len(lines)
    
    # Parse data lines
    energies_mev = []
    dedx_values = []
    
    # Pattern to match energy with unit and extract stopping power
    # SRIM format is typically: "10.00 keV   1.234E+02  5.678E+01 ..."
    line_pattern = re.compile(
        r'^\s*([\d.]+)\s*([kMGT]?eV)\s+'  # Energy with unit
        r'([\d.E+-]+)\s*'  # Electronic stopping (first stopping column)
    )
    
    for line in lines[data_start_idx:data_end_idx]:
        if not line.strip():
            continue
            
        match = line_pattern.match(line)
        if match:
            energy_val = float(match.group(1))
            energy_unit = match.group(2)
            dedx_val = float(match.group(3))
            
            # Convert energy to MeV
            energy_mev = _convert_to_mev(energy_val, energy_unit)
            
            energies_mev.append(energy_mev)
            dedx_values.append(dedx_val)
    
    if len(energies_mev) == 0:
        raise ValueError("No data points found in SRIM output. "
                        "Please check the file format.")
    
    # Create DataFrame
    df = pd.DataFrame({
        'Energy_MeV': energies_mev,
        'dE_dx': dedx_values
    })
    
    # Sort by energy (should already be sorted, but ensure it)
    df = df.sort_values('Energy_MeV').reset_index(drop=True)
    
    return df


def _convert_to_mev(value: float, unit: str) -> float:
    """
    Convert energy value to MeV based on unit string.
    
    Parameters
    ----------
    value : float
        Numeric energy value
    unit : str
        Energy unit (eV, keV, MeV, GeV, TeV)
        
    Returns
    -------
    float
        Energy in MeV
    """
    unit = unit.strip().lower()
    
    conversion_factors = {
        'ev': 1e-6,
        'kev': 1e-3,
        'mev': 1.0,
        'gev': 1e3,
        'tev': 1e6
    }
    
    if unit not in conversion_factors:
        raise ValueError(f"Unknown energy unit: {unit}")
    
    return value * conversion_factors[unit]


def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that the parsed DataFrame has the required structure.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate
        
    Returns
    -------
    bool
        True if valid
        
    Raises
    ------
    ValueError
        If validation fails
    """
    required_columns = ['Energy_MeV', 'dE_dx']
    
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame must contain columns: {required_columns}")
    
    if len(df) == 0:
        raise ValueError("DataFrame is empty")
    
    if df['Energy_MeV'].min() < 0:
        raise ValueError("Energy values must be non-negative")
    
    if df['dE_dx'].min() < 0:
        raise ValueError("dE/dx values must be non-negative")
    
    return True
