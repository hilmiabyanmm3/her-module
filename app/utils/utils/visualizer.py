import io
import openpyxl
import zipfile
import matplotlib.pyplot as plt
import numpy as np

def generate_her_free_energy_diagram(zip_bytes: bytes, applied_U: float = 0.0):
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zin:
        excel_files = [f for f in zin.namelist() if f.endswith(".xlsx")]
        if not excel_files:
            return None, "No excel file located.", None

        wb = openpyxl.load_workbook(io.BytesIO(zin.read(excel_files[0])))
        ws5 = wb['5-gibbs']
        dg_h_u0 = ws5.cell(2, 3).value

        if dg_h_u0 is None:
            return None, "Gibbs free energy not yet populated in sheet 5-gibbs.", None

        # Potential shift: Delta G(U) = Delta G(U=0) - e*U
        dg_h_u = dg_h_u0 - applied_U

        # Reaction coordinates:
        # Step 0: * + H+ + e-  -> 0.0 eV
        # Step 1: *H           -> dg_h_u
        # Step 2: * + 0.5 H2   -> - applied_U
        g_coords = [0.0, dg_h_u, -applied_U]
        steps = ["* + H⁺ + e⁻", "H*", "* + ½ H₂(g)"]

        # Plot Free Energy Diagram
        fig, ax = plt.subplots(figsize=(7, 4.8), dpi=150)
        line_len = 0.4
        for i, val in enumerate(g_coords):
            ax.plot([i - line_len/2, i + line_len/2], [val, val], color='#007BFF', lw=3)
            if i < len(g_coords) - 1:
                ax.plot([i + line_len/2, i + 1 - line_len/2], [val, g_coords[i+1]],
                        color='#adb5bd', lw=1.5, ls='--')

        ax.set_xticks(range(3))
        ax.set_xticklabels(steps, fontsize=10, fontweight='bold')
        ax.set_ylabel("Free Energy $\\Delta G$ (eV)", fontsize=11, fontweight='bold')
        ax.set_title(f"HER Free Energy Diagram (U = {applied_U:.2f} V vs RHE)", fontsize=12, fontweight='bold')
        ax.grid(axis='y', ls=':', alpha=0.6)
        plt.tight_layout()

        # Save figure to in-memory PNG
        fig_bytes = io.BytesIO()
        fig.savefig(fig_bytes, format='png', dpi=300)
        plt.close(fig)

        # Overpotential & PDS analysis
        delta_volmer = dg_h_u0
        delta_heyrovsky = -dg_h_u0

        if delta_volmer >= 0:
            pds_step = "Volmer (* + H⁺ + e⁻ → H*)"
            overpotential = delta_volmer
            prescription = "Weak hydrogen adsorption (ΔG_H* > 0). Strengthen binding by tuning d-band center or site reactivity."
        else:
            pds_step = "Heyrovsky / Tafel (H* + H⁺ + e⁻ → * + H₂)"
            overpotential = abs(delta_volmer)
            prescription = "Overly strong hydrogen binding (ΔG_H* < 0). Decrease adsorption strength to prevent catalyst poisoning."

        analysis = {
            "pds_step": pds_step,
            "overpotential": overpotential,
            "prescription": prescription
        }

        # Package into new zip
        out_zip = io.BytesIO()
        surface_name = excel_files[0].split("/")[0]
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            zout.writestr(f"{surface_name}/5-data-visual/HER_free_energy_profile_U{applied_U:.2f}V.png", fig_bytes.getvalue())

    # Re-instantiate figure for Streamlit display
    fig_display, ax_d = plt.subplots(figsize=(7, 4.8), dpi=150)
    for i, val in enumerate(g_coords):
        ax_d.plot([i - line_len/2, i + line_len/2], [val, val], color='#007BFF', lw=3)
        if i < len(g_coords) - 1:
            ax_d.plot([i + line_len/2, i + 1 - line_len/2], [val, g_coords[i+1]],
                      color='#adb5bd', lw=1.5, ls='--')
    ax_d.set_xticks(range(3))
    ax_d.set_xticklabels(steps, fontsize=10, fontweight='bold')
    ax_d.set_ylabel("Free Energy $\\Delta G$ (eV)", fontsize=11, fontweight='bold')
    ax_d.set_title(f"HER Free Energy Diagram (U = {applied_U:.2f} V vs RHE)", fontsize=12, fontweight='bold')
    ax_d.grid(axis='y', ls=':', alpha=0.6)
    plt.tight_layout()

    return fig_display, analysis, out_zip.getvalue()
