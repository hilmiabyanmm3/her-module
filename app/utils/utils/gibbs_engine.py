import io
import openpyxl
import zipfile

def calculate_her_gibbs(zip_bytes: bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zin:
        excel_files = [f for f in zin.namelist() if f.endswith(".xlsx")]
        if not excel_files:
            return False, "Excel workbook not found in workspace archive.", None

        wb = openpyxl.load_workbook(io.BytesIO(zin.read(excel_files[0])))
        ws1 = wb['1-adsorbate']
        ws2 = wb['2-isolated-mol']
        ws3 = wb['3-ads-energy']
        ws4 = wb['4-vibrasi']
        ws5 = wb['5-gibbs']

        surface_name = ws1.cell(2, 1).value or "Surface"
        eads = ws3.cell(2, 2).value
        zpe_h = ws4.cell(2, 3).value or 0.24  # Standard H* ZPE

        # Gas phase standard values (H2(g)): ZPE = 0.27 eV, TS = 0.41 eV at 298.15K
        zpe_h2 = 0.27
        ts_h2 = 0.41

        # Delta ZPE = ZPE(H*) - 0.5 * ZPE(H2)
        delta_zpe = zpe_h - 0.5 * zpe_h2
        # Delta S ≈ - 0.5 * S(H2) -> - T Delta S ≈ + 0.5 * TS(H2)
        minus_t_delta_s = 0.5 * ts_h2

        correction = delta_zpe + minus_t_delta_s
        delta_g_h = (eads if eads else 0.0) + correction

        # Populate Sheet 5
        ws5.cell(2, 1, value=surface_name)
        ws5.cell(2, 2, value="H*")
        ws5.cell(2, 3, value=round(delta_g_h, 4))

        out_zip = io.BytesIO()
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename != excel_files[0]:
                    zout.writestr(item, zin.read(item.filename))
            wb_bytes = io.BytesIO()
            wb.save(wb_bytes)
            zout.writestr(excel_files[0], wb_bytes.getvalue())

        results = {
            "surface": surface_name,
            "delta_E_dft": eads if eads else 0.0,
            "correction_term": correction,
            "delta_G_H": delta_g_h
        }

    return True, results, out_zip.getvalue()
