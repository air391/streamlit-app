"""
Birks' Law Calculator - Streamlit Application

This application calculates the quenching effect in scintillator materials
using Birks' Law and SRIM stopping power data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from pathlib import Path

# Import local modules
from srim_parser import parse_srim_text, validate_dataframe
from physics import BirksCalculator


# Page configuration
st.set_page_config(
    page_title="Birks' Law Calculator",
    page_icon="⚛️",
    layout="wide"
)


def load_presets():
    """Load preset SRIM data from JSON file."""
    preset_file = Path(__file__).parent / "presets.json"
    with open(preset_file, 'r') as f:
        return json.load(f)


def create_dataframe_from_preset(preset_data):
    """Convert preset JSON data to DataFrame."""
    data_points = preset_data['data_points']
    df = pd.DataFrame(data_points, columns=['Energy_MeV', 'dE_dx'])
    return df


def plot_stopping_power(df, title="Stopping Power vs Energy"):
    """Create a Plotly plot of dE/dx vs Energy."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Energy_MeV'],
        y=df['dE_dx'],
        mode='lines+markers',
        name='dE/dx',
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Energy (MeV)",
        yaxis_title="dE/dx (MeV/mm)",
        hovermode='closest',
        template='plotly_white',
        height=400
    )
    
    return fig


def main():
    st.title("⚛️ Birks' Law Calculator for Scintillators")
    
    st.markdown("""
    This application calculates the quenching effect in scintillator materials using **Birks' Law**:
    
    $$
    \\frac{dL}{dx} = S \\cdot \\frac{dE/dx}{1 + k_B \\cdot dE/dx}
    $$
    
    where $k_B$ is the Birks constant describing the quenching effect.
    """)
    
    # Sidebar for data input
    st.sidebar.header("Data Input")
    
    data_source = st.sidebar.radio(
        "Select Data Source:",
        ["Load Preset", "Upload SRIM File"]
    )
    
    df = None
    description = ""
    
    if data_source == "Load Preset":
        presets = load_presets()
        preset_names = list(presets.keys())
        
        selected_preset = st.sidebar.selectbox(
            "Choose Preset:",
            preset_names
        )
        
        if selected_preset:
            preset_data = presets[selected_preset]
            description = preset_data['description']
            df = create_dataframe_from_preset(preset_data)
            
            st.sidebar.success(f"✓ Loaded: {selected_preset}")
            st.sidebar.info(f"📝 {description}")
            st.sidebar.metric("Data Points", len(df))
    
    else:  # Upload SRIM File
        uploaded_file = st.sidebar.file_uploader(
            "Upload SRIM Output File (.txt)",
            type=['txt'],
            help="Upload a SRIM output file containing Energy and dE/dx columns"
        )
        
        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode('utf-8')
                df = parse_srim_text(content)
                validate_dataframe(df)
                
                st.sidebar.success(f"✓ File parsed successfully!")
                st.sidebar.metric("Data Points", len(df))
                
            except Exception as e:
                st.sidebar.error(f"Error parsing file: {str(e)}")
                st.stop()
    
    # Main content area
    if df is None:
        st.info("👈 Please select a data source from the sidebar to begin.")
        st.stop()
    
    # Display stopping power plot
    st.subheader("📊 Stopping Power Data")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig = plot_stopping_power(df, title="Electronic Stopping Power (dE/dx) vs Energy")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Data Summary**")
        st.metric("Energy Range", f"{df['Energy_MeV'].min():.4f} - {df['Energy_MeV'].max():.2f} MeV")
        st.metric("Max dE/dx", f"{df['dE_dx'].max():.2f} MeV/mm")
        st.metric("Points", len(df))
    
    # Initialize calculator
    calculator = BirksCalculator(df)
    
    st.markdown("---")
    
    # Create tabs for different calculation modes
    tab1, tab2 = st.tabs(["🔬 Forward Calculation", "🔄 Inverse Solver"])
    
    with tab1:
        st.subheader("Forward Calculation: Energy → Light Output")
        st.markdown("""
        Calculate the **visible energy** (light output) given the particle's initial energy and the Birks constant.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            particle_energy = st.number_input(
                "Particle Energy (MeV)",
                min_value=0.001,
                max_value=float(df['Energy_MeV'].max()),
                value=1.0,
                step=0.1,
                format="%.3f",
                help="Initial kinetic energy of the particle"
            )
        
        with col2:
            kb_um_mev = st.number_input(
                "Birks Constant kB (µm/MeV)",
                min_value=0.0,
                max_value=1000.0,
                value=10.0,
                step=1.0,
                format="%.2f",
                help="Birks constant in micrometers per MeV (typical range: 5-20 µm/MeV)"
            )
        
        if st.button("Calculate Visible Energy", type="primary"):
            # Convert µm/MeV to mm/MeV
            kb_mm_mev = kb_um_mev / 1000.0
            
            try:
                visible_energy_mev = calculator.calculate_visible_energy(
                    particle_energy, kb_mm_mev
                )
                quenching_factor = calculator.calculate_quenching_factor(
                    particle_energy, kb_mm_mev
                )
                
                # Display results
                st.success("✓ Calculation Complete")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Visible Energy",
                        f"{visible_energy_mev * 1000:.2f} keVee",
                        help="Light output in electron-equivalent energy"
                    )
                
                with col2:
                    st.metric(
                        "Quenching Factor",
                        f"{quenching_factor:.4f}",
                        help="Ratio of visible to deposited energy"
                    )
                
                with col3:
                    st.metric(
                        "Energy Loss",
                        f"{(1 - quenching_factor) * 100:.2f}%",
                        help="Percentage of energy lost to quenching"
                    )
                
                # Additional info
                st.info(f"""
                **Interpretation:** A particle with {particle_energy:.3f} MeV kinetic energy 
                produces {visible_energy_mev * 1000:.2f} keVee of light, corresponding to a 
                quenching factor of {quenching_factor:.4f}.
                """)
                
            except Exception as e:
                st.error(f"Calculation error: {str(e)}")
    
    with tab2:
        st.subheader("Inverse Solver: Light Output → Birks Constant")
        st.markdown("""
        **Solve for the Birks constant** given the particle's initial energy and the observed light output.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            particle_energy_inv = st.number_input(
                "Particle Energy (MeV)",
                min_value=0.001,
                max_value=float(df['Energy_MeV'].max()),
                value=1.0,
                step=0.1,
                format="%.3f",
                key="inv_energy",
                help="Initial kinetic energy of the particle"
            )
        
        with col2:
            observed_energy_kev = st.number_input(
                "Observed Light Output (keVee)",
                min_value=0.1,
                max_value=float(particle_energy_inv * 1000),
                value=500.0,
                step=10.0,
                format="%.1f",
                help="Measured visible energy in electron-equivalent keV"
            )
        
        if st.button("Solve for kB", type="primary"):
            observed_energy_mev = observed_energy_kev / 1000.0
            
            try:
                kb_mm_mev = calculator.solve_kb(
                    particle_energy_inv,
                    observed_energy_mev
                )
                kb_um_mev_result = kb_mm_mev * 1000.0
                
                # Verify the solution
                verify_energy = calculator.calculate_visible_energy(
                    particle_energy_inv, kb_mm_mev
                )
                quenching_factor = verify_energy / particle_energy_inv
                
                # Display results
                st.success("✓ Solution Found")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Birks Constant",
                        f"{kb_um_mev_result:.3f} µm/MeV",
                        help="Solved Birks constant in micrometers per MeV"
                    )
                
                with col2:
                    st.metric(
                        "Birks Constant",
                        f"{kb_mm_mev:.6f} mm/MeV",
                        help="Solved Birks constant in millimeters per MeV"
                    )
                
                with col3:
                    st.metric(
                        "Quenching Factor",
                        f"{quenching_factor:.4f}",
                        help="Resulting quenching factor"
                    )
                
                # Verification
                error_percent = abs(verify_energy * 1000 - observed_energy_kev) / observed_energy_kev * 100
                
                st.info(f"""
                **Solution:** For a {particle_energy_inv:.3f} MeV particle producing 
                {observed_energy_kev:.1f} keVee of light, the Birks constant is 
                **kB = {kb_um_mev_result:.3f} µm/MeV** ({kb_mm_mev:.6f} mm/MeV).
                
                **Verification:** Calculated energy = {verify_energy * 1000:.2f} keVee 
                (error: {error_percent:.4f}%)
                """)
                
            except ValueError as e:
                st.error(f"No solution found: {str(e)}")
            except Exception as e:
                st.error(f"Solver error: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    ### About Birks' Law
    
    Birks' Law describes the saturation of light output in scintillators for heavily ionizing particles.
    The Birks constant $k_B$ is a material-specific parameter that quantifies this quenching effect.
    
    **Typical Birks Constants:**
    - Organic scintillators: 0.01-0.02 mm/MeV (10-20 µm/MeV)
    - Inorganic scintillators: 0.005-0.015 mm/MeV (5-15 µm/MeV)
    
    **References:**
    - Birks, J. B. (1964). *The Theory and Practice of Scintillation Counting*
    - Ziegler, J. F. *SRIM - The Stopping and Range of Ions in Matter*
    """)


if __name__ == "__main__":
    main()
