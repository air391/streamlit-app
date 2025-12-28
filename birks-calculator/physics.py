"""
Physics Module for Birks' Law Calculations
Handles interpolation, integration, and root finding for quenching calculations.
"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.integrate import quad
from scipy.optimize import brentq


class BirksCalculator:
    """
    Calculator for Birks' Law quenching effect in scintillators.
    
    Birks' Law describes the non-linear response of scintillators to highly
    ionizing particles due to quenching effects:
    
    dL/dx = S * dE/dx / (1 + kB * dE/dx)
    
    where:
    - dL/dx: Light yield per unit path length
    - dE/dx: Energy loss per unit path length (stopping power)
    - kB: Birks constant (material-dependent quenching parameter)
    - S: Scintillation efficiency constant
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'Energy_MeV' and 'dE_dx'
        Must be sorted by energy in ascending order
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the calculator with stopping power data.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with 'Energy_MeV' and 'dE_dx' columns
        """
        # Ensure the dataframe is sorted by energy
        df = df.sort_values('Energy_MeV').reset_index(drop=True)
        
        # Add point at origin if not present
        if df['Energy_MeV'].iloc[0] > 0:
            df_origin = pd.DataFrame({
                'Energy_MeV': [0.0],
                'dE_dx': [0.0]
            })
            df = pd.concat([df_origin, df], ignore_index=True)
        
        self.energy = df['Energy_MeV'].values
        self.dedx = df['dE_dx'].values
        
        # Create interpolation function for dE/dx vs Energy
        # Using linear interpolation with extrapolation
        self.dedx_interp = interp1d(
            self.energy,
            self.dedx,
            kind='linear',
            bounds_error=False,
            fill_value='extrapolate'
        )
        
        self.max_energy = self.energy[-1]
        self.min_energy = self.energy[0]
    
    def get_dedx(self, energy_mev: float) -> float:
        """
        Get dE/dx value at a specific energy using interpolation.
        
        Parameters
        ----------
        energy_mev : float
            Energy in MeV
            
        Returns
        -------
        float
            dE/dx value at the given energy
        """
        return float(self.dedx_interp(energy_mev))
    
    def calculate_visible_energy(self, initial_energy_mev: float, kb_mm_mev: float) -> float:
        """
        Calculate the visible (light) energy for a particle with given initial energy.
        
        Forward calculation: Integrate Birks' Law from 0 to initial_energy
        to find the total light output (visible energy).
        
        The visible energy is calculated as:
        E_visible = ∫[0 to E_init] dE / (1 + kB * dE/dx(E))
        
        Parameters
        ----------
        initial_energy_mev : float
            Initial particle energy in MeV
        kb_mm_mev : float
            Birks constant in mm/MeV
            
        Returns
        -------
        float
            Visible energy in MeV (MeVee - electron equivalent energy)
        """
        if initial_energy_mev <= 0:
            return 0.0
        
        if kb_mm_mev < 0:
            raise ValueError("Birks constant must be non-negative")
        
        # Define the integrand: 1 / (1 + kB * dE/dx)
        def integrand(E):
            dedx_val = self.get_dedx(E)
            # Avoid division by zero or negative denominators
            denom = 1.0 + kb_mm_mev * dedx_val
            if denom <= 0:
                return 0.0
            return 1.0 / denom
        
        # Integrate from 0 to initial_energy
        try:
            visible_energy, error = quad(
                integrand,
                0.0,
                initial_energy_mev,
                limit=100,
                epsabs=1e-6,
                epsrel=1e-6
            )
            return visible_energy
        except Exception as e:
            raise RuntimeError(f"Integration failed: {str(e)}")
    
    def calculate_quenching_factor(self, initial_energy_mev: float, kb_mm_mev: float) -> float:
        """
        Calculate the quenching factor (QF).
        
        QF = E_visible / E_initial
        
        Parameters
        ----------
        initial_energy_mev : float
            Initial particle energy in MeV
        kb_mm_mev : float
            Birks constant in mm/MeV
            
        Returns
        -------
        float
            Quenching factor (dimensionless, between 0 and 1)
        """
        if initial_energy_mev <= 0:
            return 0.0
        
        visible_energy = self.calculate_visible_energy(initial_energy_mev, kb_mm_mev)
        return visible_energy / initial_energy_mev
    
    def solve_kb(self, initial_energy_mev: float, observed_energy_mev: float,
                 kb_min: float = 0.0, kb_max: float = 0.5) -> float:
        """
        Inverse calculation: Find the Birks constant that produces the observed energy.
        
        Given initial energy and observed (visible) energy, solve for kB such that:
        calculate_visible_energy(initial_energy, kB) = observed_energy
        
        Parameters
        ----------
        initial_energy_mev : float
            Initial particle energy in MeV
        observed_energy_mev : float
            Observed visible energy in MeV (MeVee)
        kb_min : float, optional
            Minimum kB value for search range (mm/MeV), default 0.0
        kb_max : float, optional
            Maximum kB value for search range (mm/MeV), default 0.5
            
        Returns
        -------
        float
            Birks constant in mm/MeV
            
        Raises
        ------
        ValueError
            If no solution exists in the given range or if inputs are invalid
        """
        if initial_energy_mev <= 0:
            raise ValueError("Initial energy must be positive")
        
        if observed_energy_mev <= 0:
            raise ValueError("Observed energy must be positive")
        
        if observed_energy_mev > initial_energy_mev:
            raise ValueError("Observed energy cannot exceed initial energy (QF must be ≤ 1)")
        
        # Special case: if observed equals initial, kB = 0
        if abs(observed_energy_mev - initial_energy_mev) < 1e-9:
            return 0.0
        
        # Define the objective function
        def objective(kb):
            calc_energy = self.calculate_visible_energy(initial_energy_mev, kb)
            return calc_energy - observed_energy_mev
        
        # Check if solution exists in the range
        f_min = objective(kb_min)
        f_max = objective(kb_max)
        
        if f_min * f_max > 0:
            # No sign change, try extending the range
            if f_max > 0:
                # Need larger kB
                kb_max = 2.0
                f_max = objective(kb_max)
                if f_max > 0:
                    raise ValueError(
                        f"No solution found. Maximum kB of {kb_max} mm/MeV still gives "
                        f"visible energy > observed energy. Try increasing kb_max or "
                        f"check your input values."
                    )
            else:
                raise ValueError(
                    "No solution found in the range. Observed energy may be too close to "
                    "initial energy (requires kB ≈ 0)."
                )
        
        # Use Brent's method to find the root
        try:
            kb_solution = brentq(
                objective,
                kb_min,
                kb_max,
                xtol=1e-8,
                rtol=1e-8,
                maxiter=100
            )
            return kb_solution
        except Exception as e:
            raise RuntimeError(f"Root finding failed: {str(e)}")
    
    def get_energy_range(self):
        """
        Get the valid energy range of the stopping power data.
        
        Returns
        -------
        tuple
            (min_energy, max_energy) in MeV
        """
        return (self.min_energy, self.max_energy)
