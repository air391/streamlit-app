from typing import Literal
import streamlit as st
import numpy as np
import plotly.express as px
from utils import generate_controls
from cal import (
    generate_points,
    filter_points_in_box,
    generate_directions,
    box_intersection_length,
)

# Initialize session state for data storage
if "data_store" not in st.session_state:
    st.session_state.data_store = []
if "labels_store" not in st.session_state:
    st.session_state.labels_store = []


def data_gen(
    a: float = 3.8,
    b: float = 3.8,
    c: float = 1,
    type: Literal["box", "sphere"] = "box",
    space: Literal["space", "half space"] = "space",
):
    """
    Generate data

    Args:
        a : x length of GAGG
        b : y length of GAGG
        c : z length of GAGG
        type : Type of get the sample point
        space : space of the sample point
    Returns:
        np.ndarray: length in GAGG
    """
    num_gen = 100_0000
    n = 5
    if space == "space":
        box_min = np.array([-a / 2, -b / 2, -c / 2])
        box_max = np.array([a / 2, b / 2, c / 2])
    elif space == "half space":
        box_min = np.array([-a / 2, -b / 2, -c])
        box_max = np.array([a / 2, b / 2, 0])
    else:
        raise ValueError("space must be 'space' or 'half space'")
    if type == "box":
        origin = generate_points(num_gen, n * box_min, n * box_max)
    elif type == "sphere":
        origin = generate_directions(num_gen, half=space == "half space") * a
    else:
        raise ValueError("type must be 'box' or 'sphere'")
    origin_filter = filter_points_in_box(origin, box_min, box_max)
    num_got = origin_filter.shape[0]
    direction = generate_directions(num_got)
    length = box_intersection_length(origin_filter, direction, box_min, box_max)
    length_filter = length[length > 0]
    return length_filter


def plot_gen(
        data: np.ndarray,
        labels: list,
        bin_size: int = 30,
        histnorm: Literal["", "percent", "density", "probability", "probability density"] = ""):
    """
    Generate a Plotly histogram based on the provided data.

    Args:
        data (list of np.ndarray): List of datasets to plot.
        labels (list of str): Corresponding labels for the datasets.
        bin_size (int): Number of bins for the histogram.
        histnorm (Literal["", "percent", "density"]): Normalization for histogram bars.

    Returns:
        plotly.graph_objects.Figure: The generated histogram.
    """
    combined_data = []
    combined_labels = []
    for dataset, label in zip(data, labels):
        combined_data.extend(dataset)
        combined_labels.extend([label] * len(dataset))

    fig = px.histogram(
        x=combined_data, 
        color=combined_labels, 
        labels={'x': 'Value', 'color': 'Dataset'}, 
        nbins=bin_size, 
        histnorm=histnorm
    )
    return fig



def main():
    st.title("Histogram of GCR in rectangular cuboid")

    st.write(
        "This application generates an isotropic particle source in space and calculates the length of the particles passing through the cuboid."
    )

    # Generate controls for data_gen
    st.sidebar.header("Simulation Parameters")
    gen_params = generate_controls(data_gen)

    # Additional controls for histogram
    st.sidebar.header("Histogram Parameters")
    bin_size = st.sidebar.slider("Bin Size", min_value=10, max_value=100, value=30, step=5)
    histnorm = st.sidebar.selectbox("Normalization", ["", "percent", "density", "probability", "probability density"], index=0)

    # Generate new data and add to store
    if st.button("Generate and Add Data"):
        data = data_gen(**gen_params)
        label = f"a={gen_params['a']}, b={gen_params['b']}, c={gen_params['c']}, type={gen_params['type']}, space={gen_params['space']}"
        st.session_state.data_store.append(data)
        st.session_state.labels_store.append(label)
        st.success("Data added to the global list!")

    # Select specific datasets to display
    if st.session_state.data_store:
        st.sidebar.header("Select Data to Plot")
        selected_labels = st.sidebar.multiselect(
            "Select datasets to include:",
            st.session_state.labels_store,
            default=st.session_state.labels_store,
        )

        selected_data = [
            st.session_state.data_store[i]
            for i, label in enumerate(st.session_state.labels_store)
            if label in selected_labels
        ]

        # Plot selected data
        fig = plot_gen(selected_data, selected_labels, bin_size=bin_size, histnorm=histnorm)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data available. Generate data to start plotting.")


if __name__ == "__main__":
    main()
