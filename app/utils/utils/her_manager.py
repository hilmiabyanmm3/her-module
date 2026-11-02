import io
import re
import zipfile
import openpyxl
import numpy as np
from ase.io import read
from ase.data import atomic_numbers

RY_TO_EV = 13.6056980659

def create_initial_workspace_zip(surface_name: str) -> bytes:
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Base directories
        zf.writestr(f"{surface_name}/1-surface/", "")
        zf.writestr(f"{surface_name}/2-isolated-gas/h2/", "")
        zf.writestr(f"{surface_name}/2-isolated-gas/h2o/", "")
        zf.writestr(f"{surface_name}/3-adsorption/h/", "")
        zf.writestr(f"{surface_name}/4-vibration/h/", "")
        zf.writestr(f"{surface_name}/5-data-visual/", "")

        # 2. Add isolated gas templates
        with open("templates/c-isolated_h2.in", "r") as f:
            zf.writestr(f"{surface_name}/2-isolated-gas/h2/isolated_h2.in", f.read())
        with open("templates/c-isolated_h2o.in", "r") as f:
            zf.writestr(f"{surface_name}/2-isolated-gas/h2o/isolated_h2o.in", f.read())

        # 3. Create Excel workbook and populate headers
        wb = openpyxl.load_workbook("templates/d-her_data_sheet.xlsx")
        for sname in wb.sheetnames:
            ws = wb[sname]
            for r in range(1, ws.max_row + 1):
                for c in range(1, ws.max_column + 1):
                    if ws.cell(r, c).value == "surface":
                        ws.cell(r + 1, c, value=surface_name)

        wb_bytes = io.BytesIO()
        wb.save(wb_bytes)
        zf.writestr(f"{surface_name}/{surface_name}_her_data_sheet.xlsx", wb_bytes.getvalue())

    return mem_zip.getvalue()

def inspect_surface_file(zip_bytes: bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        in_file = [f for f in zf.namelist() if "/1-surface/" in f and f.endswith(".in") and not f.startswith("__MACOSX")]
        out_file = [f for f in zf.namelist() if "/1-surface/" in f and f.endswith(".out") and not f.startswith("__MACOSX")]

        if not in_file or not out_file:
            return None, None, None, None, None

        surface_name = in_file[0].split("/")[0]
        in_content = zf.read(in_file[0]).decode("utf-8", errors="ignore")
        out_content = zf.read(out_file[0]).decode("utf-8", errors="ignore")

        atoms = read(io.StringIO(out_content), format="espresso-out")
        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()

        z_coords = positions[:, 2]
        max_z = np.max(z_coords)
        top_mask = z_coords >= (max_z - 2.0)

        sites = []
        for i, (sym, pos, is_top) in enumerate(zip(symbols, positions, top_mask)):
            if is_top and sym in ['Pt', 'Ni', 'Fe', 'Co', 'Cu', 'Mo', 'W', 'N', 'C', 'P', 'S']:
                sites.append({
                    "index": i + 1,
                    "symbol": sym,
                    "x": float(pos[0]),
                    "y": float(pos[1]),
                    "z": float(pos[2]),
                    "layer": "Top"
                })

        return surface_name, sites, atoms, in_content, out_content

def generate_adsorbate_structure(zip_bytes: bytes, surface_name: str, target_site_index: int, h_distance: float = 1.0) -> bytes:
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zin:
        with zipfile.ZipFile(mem_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))

            in_file = [f for f in zin.namelist() if "/1-surface/" in f and f.endswith(".in")][0]
            out_file = [f for f in zin.namelist() if "/1-surface/" in f and f.endswith(".out")][0]
            in_content = zin.read(in_file).decode("utf-8")
            out_content = zin.read(out_file).decode("utf-8")

            atoms = read(io.StringIO(out_content), format="espresso-out")
            target_pos = atoms.positions[target_site_index - 1]
            h_pos = [target_pos[0], target_pos[1], target_pos[2] + h_distance]

            new_in = _inject_adsorbate_pw(in_content, atoms, h_pos)
            zout.writestr(f"{surface_name}/3-adsorption/h/h-adsorbate.in", new_in)

            # Update excel sheet 1
            excel_files = [f for f in zin.namelist() if f.endswith(".xlsx")]
            if excel_files:
                wb = openpyxl.load_workbook(io.BytesIO(zin.read(excel_files[0])))
                ws = wb['1-adsorbate']
                energy_ry = _extract_final_scf(out_content)
                ws.cell(2, 1, value=surface_name)
                if energy_ry:
                    ws.cell(2, 2, value=energy_ry)
                    ws.cell(2, 3, value=energy_ry * RY_TO_EV)
                wb_out = io.BytesIO()
                wb.save(wb_out)
                zout.writestr(excel_files[0], wb_out.getvalue())

    return mem_zip.getvalue()

def _extract_final_scf(content: str):
    matches = re.findall(r'!\s+total energy\s+=\s+([-+]?\d+\.\d+)\s+Ry', content)
    return float(matches[-1]) if matches else None

def _inject_adsorbate_pw(template_in: str, atoms, h_coord: list) -> str:
    lines = template_in.splitlines()
    nat_updated = len(atoms) + 1
    
    clean_lines = []
    in_positions = False
    for line in lines:
        if re.search(r'nat\s*=', line, re.IGNORECASE):
            line = re.sub(r'nat\s*=\s*\d+', f'nat = {nat_updated}', line, flags=re.IGNORECASE)
        if "ATOMIC_POSITIONS" in line:
            in_positions = True
            clean_lines.append(line)
            for atom in atoms:
                clean_lines.append(f"{atom.symbol:<4} {atom.position[0]:14.8f} {atom.position[1]:14.8f} {atom.position[2]:14.8f}")
            clean_lines.append(f"H    {h_coord[0]:14.8f} {h_coord[1]:14.8f} {h_coord[2]:14.8f}")
            continue
        if in_positions:
            if line.strip().startswith(('K_POINTS', 'CELL_PARAMETERS', '&')):
                in_positions = False
                clean_lines.append(line)
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines)

def extract_scf_energies(zip_bytes: bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zin:
        excel_files = [f for f in zin.namelist() if f.endswith(".xlsx")]
        if not excel_files:
            return False, "No Excel spreadsheet found in archive.", None

        wb = openpyxl.load_workbook(io.BytesIO(zin.read(excel_files[0])))
        ws1 = wb['1-adsorbate']
        ws2 = wb['2-isolated-mol']
        ws3 = wb['3-ads-energy']

        # h-adsorbate energy
        h_out = [f for f in zin.namelist() if "/3-adsorption/h/" in f and f.endswith(".out")]
        if h_out:
            e_h_ads = _extract_final_scf(zin.read(h_out[0]).decode("utf-8", errors="ignore"))
            if e_h_ads:
                ws1.cell(2, 4, value=e_h_ads)
                ws1.cell(2, 5, value=e_h_ads * RY_TO_EV)

        # Isolated gases
        h2_out = [f for f in zin.namelist() if "/2-isolated-gas/h2/" in f and f.endswith(".out")]
        if h2_out:
            e_h2 = _extract_final_scf(zin.read(h2_out[0]).decode("utf-8", errors="ignore"))
            if e_h2:
                ws2.cell(2, 1, value="H2_gas")
                ws2.cell(2, 2, value=e_h2 * RY_TO_EV)

        # Calculate E_ads = E_total - E_surf - 0.5*E_H2
        e_surf = ws1.cell(2, 3).value
        e_slab_h = ws1.cell(2, 5).value
        e_gas_h2 = ws2.cell(2, 2).value
        if e_surf and e_slab_h and e_gas_h2:
            eads = e_slab_h - e_surf - 0.5 * e_gas_h2
            ws3.cell(2, 1, value=ws1.cell(2, 1).value)
            ws3.cell(2, 2, value=eads)

        out_zip = io.BytesIO()
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename != excel_files[0]:
                    zout.writestr(item, zin.read(item.filename))
            wb_bytes = io.BytesIO()
            wb.save(wb_bytes)
            zout.writestr(excel_files[0], wb_bytes.getvalue())

            # Prepare vibration displacements
            surf_dir = excel_files[0].split("/")[0]
            if h_out:
                atoms_ads = read(io.StringIO(zin.read(h_out[0]).decode("utf-8")), format="espresso-out")
                _write_displacement_inputs(zout, surf_dir, atoms_ads)

    return True, "SCF energies extracted & vibration displacements generated.", out_zip.getvalue()

def _write_displacement_inputs(zout: zipfile.ZipFile, surf_dir: str, atoms, delta: float = 0.01):
    h_idx = len(atoms) - 1  # Adsorbate H
    axes = ['x', 'y', 'z']
    for ax_i, axis in enumerate(axes):
        for sign, s_label in [(1.0, 'disp_plus'), (-1.0, 'disp_minus')]:
            disp_atoms = atoms.copy()
            disp_pos = disp_atoms.positions
            disp_pos[h_idx, ax_i] += sign * delta
            disp_atoms.set_positions(disp_pos)
            
            pwi = io.StringIO()
            disp_atoms.write(pwi, format='espresso-in')
            zout.writestr(f"{surf_dir}/4-vibration/h/LOG_{axis}_{s_label}.in", pwi.getvalue())
