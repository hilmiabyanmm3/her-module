import streamlit as st
from utils.ui_components import module_header, inject_global_css, style_sidebar

inject_global_css()
style_sidebar()
module_header("📖", "Theory & Workflow Documentation", "Fundamental physics and operational user guide")

tab_her, tab_guide = st.tabs(["1. Fundamentals of HER", "2. Module Operations & Troubleshooting"])

with tab_her:
    st.markdown("""
    ### 1. What is the Hydrogen Evolution Reaction (HER)?
    HER is the cathodic half-reaction of electrochemical water splitting:
    $$2\\text{H}^+(aq) + 2e^- \\rightarrow \\text{H}_2(g)$$
    In acidic conditions, or alkaline media involving water dissociation:
    $$2\\text{H}_2\\text{O} + 2e^- \\rightarrow \\text{H}_2(g) + 2\\text{OH}^-$$

    ### 2. Mechanistic Elementary Steps
    The reaction proceeds via two competitive reaction mechanisms:
    1. **Volmer Step (Electrosorption):**
       $$* + \\text{H}^+ + e^- \\rightarrow *\\text{H}$$
    2. Followed by either:
       - **Heyrovsky Step (Electrochemical Desorption):**
         $$*\\text{H} + \\text{H}^+ + e^- \\rightarrow * + \\text{H}_2(g)$$
       - **Tafel Step (Chemical Recombination):**
         $$2*\\text{H} \\rightarrow 2* + \\text{H}_2(g)$$

    ### 3. Sabatier Principle & Volcano Relation
    The primary thermodynamic descriptor is the hydrogen chemisorption Gibbs free energy:
    - **$\\Delta G_{\\text{H*}} \\approx 0\\text{ eV}$:** Optimal electrocatalyst (e.g. Platinum).
    - **$\\Delta G_{\\text{H*}} > 0\\text{ eV}$:** Binding is too weak; Volmer step is rate-limiting.
    - **$\\Delta G_{\\text{H*}} < 0\\text{ eV}$:** Binding is too strong; Heyrovsky/Tafel desorption is poisoned.
    """)

with tab_guide:
    st.markdown("""
    ### Technical Guide & Troubleshooting

    | Module | Required Input | Produced Output | Common Errors & Resolution |
    | :--- | :--- | :--- | :--- |
    | **Mod 1** | Surface Name | Directory tree + `.xlsx` | Empty text: provide an alphanumeric slab identifier. |
    | **Mod 2** | `1-surface/*.in`, `*.out` | `3-adsorption/h/h-adsorbate.in` | No `.out` found: ensure DFT relaxation finished with `JOB DONE`. |
    | **Mod 3** | `h-adsorbate.out`, gas outputs | `4-vibration/` displacements, ZPE | Forces mismatch: verify all 6 Cartesian displacement jobs converged. |
    | **Mod 4** | Completed Excel sheets 1-4 | Sheet 5 $\\Delta G_{\\text{H*}}$ calculation | Missing gas energy: check `2-isolated-mol` sheet values. |
    | **Mod 5** | Sheet 5 Gibbs data | Figure in `5-data-visual/` | Empty figure: verify non-zero values in column `e_g_1`. |
    """)
