import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class BottleneckAnalyzer:

  def __init__(self):
    self.step_names = ["Volmer (* + H+ + e- -> *H)", "Heyrovsky (*H + H+ + e- -> * + H2)"]

  def identify_bottlenecks(self, plot_data):
    analysis_results = []
    for site_data in plot_data:
      deltas = site_data['deltaG']  # [DeltaG_Volmer, DeltaG_Heyrovsky]
      dg_h = deltas[0]  # Delta G of *H formation at U=0

      # In HER:
      # If Delta G_H* > 0: Hydrogen binding is too weak -> Volmer is limiting
      # If Delta G_H* < 0: Hydrogen binding is too strong -> Heyrovsky/Tafel desorption is limiting
      if dg_h > 0:
        pds_step = self.step_names[0]
        prescription = (
            "Hydrogen adsorption is too weak (Delta G_H* > 0). Increase"
            " surface reactivity or d-band center."
        )
      else:
        pds_step = self.step_names[1]
        prescription = (
            "Hydrogen desorption is difficult (Delta G_H* < 0). Decrease binding"
            " strength to avoid site poisoning."
        )

      analysis_results.append({
          "Site": site_data["label"],
          "Delta G_H* (eV)": round(dg_h, 3),
          "PDS Step": pds_step,
          "Overpotential (V)": round(site_data["overpotential"], 3),
          "Prescription": prescription,
      })
    return analysis_results


class GibbsAnalyzer:

  def __init__(self):
    self.ry_to_ev = 13.605698066
    self.colors = [
        "orange",
        "green",
        "blue",
        "red",
        "purple",
        "salmon",
        "pink",
        "cyan",
        "lime",
        "brown",
    ] * 3
    self.markers = ["s"] * 12 + ["^"] * 12 + ["o"] * 12

  def _clean_dataframe(self, df):
    if "Path" in df.columns:
      return df[df["Path"].notna() & (df["Path"] != "")].copy()
    return df.dropna(how="all").copy()

  def calculate_deltas(self, df_energy, df_zpe, G_H2, U=0.0):
    """Calculates HER Gibbs free energy profile under CHE model.

    G_H2: Free energy of isolated H2 molecule (eV), including ZPE and TS.
    df_energy steps expected: 'slab' and '1-h' (or 'h') df_zpe steps expected:
    '1-h' (ZPE for adsorbed H in eV)
    """
    df_e = self._clean_dataframe(df_energy)
    df_z = self._clean_dataframe(df_zpe)

    merged = pd.merge(
        df_e,
        df_z[["Step", "Site", "ZPE (eV)"]],
        on=["Step", "Site"],
        how="left",
    )
    merged["ZPE (eV)"] = merged["ZPE (eV)"].fillna(0.0)
    merged["E (eV)"] = merged["Energy (Ry)"] * self.ry_to_ev

    results = []
    # CHE: 1/2 H2 <-> H+ + e- at U = 0 V vs RHE
    G_PE = 0.5 * G_H2

    for site, group in merged.groupby(["Site"]):

      def get_val(step_name, col):
        val = group[group["Step"] == step_name][col].values
        return val[0] if len(val) > 0 else None

      # Look up clean slab and H-adsorbed slab
      E_slab = get_val("slab", "E (eV)")
      E_h = get_val("1-h", "E (eV)")
      if E_h is None:
        E_h = get_val("h", "E (eV)")

      Z_h = get_val("1-h", "ZPE (eV)")
      if Z_h is None:
        Z_h = get_val("h", "ZPE (eV)")
      if Z_h is None:
        Z_h = 0.0

      if E_slab is None or E_h is None:
        continue

      # Total Gibbs Free Energy approximations:
      # G(*H) = E(*H) + ZPE(*H) - TS(*H) (TS of adsorbed H is small, typically ~0 - 0.02 eV)
      # Delta G_H* = G(*H) - G(*) - 1/2 G(H2) - eU
      dg_volmer = (E_h + Z_h) - E_slab - G_PE - U
      dg_heyrovsky = (E_slab + G_H2) - (E_h + Z_h) - G_PE - U

      dg = [dg_volmer, dg_heyrovsky]

      # Overpotential for HER is determined by the volcano descriptor |Delta G_H*|
      overpotential = max(abs(dg_volmer), 0.0) if U == 0.0 else max(dg)

      # Energy levels: [Initial (* + H+ + e-), Intermediate (*H), Final (* + 1/2 H2)]
      levels = [0.0]
      levels.append(levels[-1] + dg[0])
      levels.append(levels[-1] + dg[1])

      dataX, dataY = [], []
      for i, l in enumerate(levels):
        dataX.extend([2 * i, 2 * i + 1])
        dataY.extend([l, l])

      results.append({
          "label": site[0] if isinstance(site, tuple) else site,
          "deltaG": dg,
          "overpotential": overpotential,
          "dataX": dataX,
          "dataY": dataY,
      })
    return results

  def create_plot(self, plot_data, title, U_shift=0.0):
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.linewidth"] = 2
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_axes([0.12, 0.12, 0.72, 0.78])

    all_shifted_y = []
    for data in plot_data:
      dg = data["deltaG"]
      y_levels = [0.0]
      # Volmer step (electron transfer)
      y_levels.append(y_levels[-1] + dg[0] - U_shift)
      # Heyrovsky step (electron transfer)
      y_levels.append(y_levels[-1] + dg[1] - U_shift)

      y_plot = []
      for l in y_levels:
        y_plot.extend([l, l])
      data["temp_y"] = y_plot
      all_shifted_y.extend(y_plot)

    ax.set_ylabel(r"$\Delta G$ (eV)", fontsize=16)
    ax.set_xlabel("Reaction Coordinate", fontsize=16)
    ax.set_xticks([])

    if all_shifted_y:
      ax.set_ylim(min(all_shifted_y) - 0.4, max(all_shifted_y) + 0.6)

    # 3 Reaction States for Volmer-Heyrovsky Pathway
    istep = ["* + H$^+$ + e$^-$", "*H", "* + $\\frac{1}{2}$H$_2$"]
    for i in range(3):
      max_y = max(d["temp_y"][2 * i] for d in plot_data)
      ax.text(
          i * 2 + 0.5,
          max_y + 0.08,
          istep[i],
          ha="center",
          fontsize=12,
          fontweight="bold",
      )

    for i, data in enumerate(plot_data):
      c = self.colors[i % len(self.colors)]
      m = self.markers[i % len(self.markers)]
      x, y = data["dataX"], data["temp_y"]

      # Connections between platforms (2 transitions)
      for j in range(2):
        ax.plot(
            [x[2 * j + 1], x[2 * j + 2]],
            [y[2 * j + 1], y[2 * j + 2]],
            color=c,
            linestyle="--",
            alpha=0.6,
        )

      # Horizontal energy levels (3 states)
      for j in range(3):
        line_label = data["label"] if j == 0 else ""
        ax.plot(
            [x[2 * j], x[2 * j + 1]],
            [y[2 * j], y[2 * j + 1]],
            color=c,
            linewidth=4,
            label=line_label,
        )
        ax.plot(
            x[2 * j] + 0.5,
            y[2 * j],
            marker=m,
            color=c,
            markeredgecolor="black",
            markersize=8,
        )

    ax.axhline(0, color="gray", linestyle=":", linewidth=1.2, alpha=0.7)
    ax.legend(
        loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, fontsize=11
    )
    ax.set_title(title, loc="left", fontsize=16, pad=15)
    return fig