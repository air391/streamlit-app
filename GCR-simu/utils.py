import inspect
import streamlit as st
from typing import Literal

def generate_controls(func):
    """
    Automatically generate Streamlit controls based on a function's signature and docstring.

    Args:
        func (callable): The function for which to generate controls.

    Returns:
        dict: A dictionary of parameter values.
    """
    params = {}
    sig = inspect.signature(func)
    doc = func.__doc__
    doc_params = {}

    if doc:
        lines = doc.splitlines()
        args_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Args:"):
                args_section = True
            elif args_section:
                if stripped == "" or stripped.startswith("Returns:"):
                    args_section = False
                else:
                    param_line = stripped.split(":", 1)
                    if len(param_line) == 2:
                        param_name, description = param_line
                        doc_params[param_name.strip()] = description.strip()


    for name, param in sig.parameters.items():
        param_type = param.annotation
        default = param.default if param.default is not inspect.Parameter.empty else None
        description = doc_params.get(name, "")

        if param_type == float:
            params[name] = st.sidebar.number_input(f"{name} ({description})", value=float(default) if default is not None else 0.0)
        elif param_type == int:
            params[name] = st.sidebar.number_input(f"{name} ({description})", value=int(default) if default is not None else 0, step=1)
        elif hasattr(param_type, "__origin__") and param_type.__origin__ == Literal:
            options = list(param_type.__args__)
            params[name] = st.sidebar.selectbox(f"{name} ({description})", options, index=options.index(default) if default in options else 0)
    return params