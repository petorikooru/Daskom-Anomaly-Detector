import os
import pickle
import pandas as pd
from enum import Enum

CACHE_FILE = "app_cache.pkl"


class Prak(Enum):
    TE = "TE"
    TE_INT = "TE_INT"
    TT = "TT"
    TT_INT = "TT_INT"
    TF = "TF"
    TB = "TB"
    TSE = "TSE"
    OTHERS = "OTHERS"


class ProcessAnomaly:
    # Rubrication rules
    VALID_TA = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100}
    VALID_D = {
        45.00,
        50.00,
        53.75,
        55.00,
        57.5,
        58.75,
        60.0,
        62.5,
        63.75,
        65.00,
        66.25,
        67.50,
        68.75,
        70.0,
        71.25,
        72.5,
        75.0,
        76.25,
        78.75,
        80.00,
        82.50,
        83.75,
        87.5,
        91.25,
        95.0,
        0.0,  # If they aren't present
    }
    VALID_I = {
        22.5,
        27.5,
        32.5,
        37.5,
        40.0,
        42.5,
        45.0,
        47.5,
        50.0,
        52.5,
        55.0,
        57.5,
        60.0,
        62.5,
        65.0,
        67.5,
        70.0,
        72.5,
        75.0,
        77.5,
        80.0,
        82.5,
        85.0,
        87.5,
        90.0,
        92.5,
        97.5,
        0.0,  # If they aren't present
    }

    def __init__(self):
        self.original_data: dict = {}
        self.loaded_data: dict = {}
        self.anomaly_data: dict = {}

        self.load_cache()

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    data = pickle.load(f)
                    self.original_data = data.get("original", {})
                    self.loaded_data = data.get("loaded", {})
            except Exception as e:
                print(f"Failed to load cache: {e}")
                self.reset()

    def save_cache(self):
        data = {"original": self.original_data, "loaded": self.loaded_data}
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def load_batch(self, type: str, file_paths: list, overwrite: bool = False):
        if overwrite:
            if type == "original":
                self.original_data.clear()
            elif type == "loaded":
                self.loaded_data.clear()
                self.anomaly_data.clear()

        for path in file_paths:
            praktikans = self.categorize_file(path)

            match type:
                case "original":
                    df = pd.read_excel(path)

                    if praktikans in self.original_data:
                        self.original_data[praktikans] = pd.concat(
                            [self.original_data[praktikans], df], ignore_index=True
                        )
                    else:
                        self.original_data[praktikans] = df

                case "loaded":
                    # Multi-level header
                    df = pd.read_excel(path, header=[0, 1])
                    df.columns = [
                        (lvl1, lvl2 if pd.notna(lvl2) else "")
                        for lvl1, lvl2 in df.columns
                    ]

                    if praktikans in self.loaded_data:
                        self.loaded_data[praktikans] = pd.concat(
                            [self.loaded_data[praktikans], df], ignore_index=True
                        )
                    else:
                        self.loaded_data[praktikans] = df

                case "anomaly" | _:
                    pass

        self.save_cache()

    def categorize_file(self, file_path: str) -> Prak:
        PRAKTIKANS = {
            "TT_INT": Prak.TT_INT,
            "TE_INT": Prak.TE_INT,
            "TT": Prak.TT,
            "TE": Prak.TE,
            "TF": Prak.TF,
            "TB": Prak.TB,
            "TSE": Prak.TSE,
        }
        base = os.path.basename(file_path)
        name_without_ext, _ = os.path.splitext(base)
        name_upper = name_without_ext.upper()

        for suffix, category in PRAKTIKANS.items():
            if name_upper.endswith(suffix):
                return category
        return Prak.OTHERS

    @staticmethod
    def get_available_modules(df: pd.DataFrame) -> list:
        """Extract module names from column headers, ignoring empty/unnamed ones."""
        modules = set()
        for col in df.columns:
            if isinstance(col, tuple) and len(col) == 2:
                module_name = col[0]

                if pd.notna(module_name) and str(module_name).strip():
                    mod_str = str(module_name).strip().lower()

                    if not any(
                        keyword in mod_str
                        for keyword in ["nim", "nama", "nma", "no", "unnamed"]
                    ):
                        modules.add(str(module_name).strip())

        return sorted(list(modules))

    @staticmethod
    def is_valid(parameter, value):
        if pd.isna(value):
            return True
        try:
            value = float(value)
        except:
            return False

        match parameter:
            case "TP":
                return 1 <= value <= 100
            case "I":
                return value in ProcessAnomaly.VALID_I
            case "TA":
                return value in ProcessAnomaly.VALID_TA
            case "D":
                return value in ProcessAnomaly.VALID_D
        return True

    @staticmethod
    def is_zero(value):
        try:
            return float(value) == 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_empty(value):
        return pd.isna(value) or str(value).strip() == ""

    def analyze(self, selected_modules: list):
        self.anomaly_data = {}

        for prakt, df in self.loaded_data.items():
            invalid_data = []
            orig_df = self.get_original(prakt)

            try:
                nim_col = next(
                    col for col in df.columns if "nim" in str(col[0]).lower()
                )
                nama_col = next(
                    col
                    for col in df.columns
                    if "nama" in str(col[0]).lower() or "nma" in str(col[0]).lower()
                )
            except StopIteration:
                print(
                    f"❌ Could not find NIM/Nama in loaded data for {prakt.value}. Skipping analysis."
                )
                self.anomaly_data[prakt] = pd.DataFrame()
                continue

            if not orig_df.empty:
                try:
                    orig_nama_col = next(
                        col
                        for col in orig_df.columns
                        if "nama" in str(col).lower() or "nma" in str(col).lower()
                    )
                    orig_nim_col = next(
                        (col for col in orig_df.columns if "nim" in str(col).lower()),
                        None,
                    )

                    orig_names = set(
                        orig_df[orig_nama_col]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .str.lower()
                    )
                    orig_names.discard("")
                    orig_names.discard("nan")

                    loaded_names = set(
                        df[nama_col].dropna().astype(str).str.strip().str.lower()
                    )
                    loaded_names.discard("")
                    loaded_names.discard("nan")

                    missing_names = orig_names - loaded_names
                    extra_names = loaded_names - orig_names

                    for m_name in missing_names:
                        match_row = orig_df[
                            orig_df[orig_nama_col].astype(str).str.strip().str.lower()
                            == m_name
                        ].iloc[0]
                        original_nama = match_row[orig_nama_col]
                        nim_val = match_row[orig_nim_col] if orig_nim_col else "-"

                        invalid_data.append(
                            {
                                "Class": prakt.value,
                                "Row": "-",
                                "NIM": nim_val,
                                "Nama": original_nama,
                                "Module": "N/A",
                                "Parameter": "Missing Student (?)",
                                "Value": "Not in loaded file",
                            }
                        )

                    for e_name in extra_names:
                        match_row = df[
                            df[nama_col].astype(str).str.strip().str.lower() == e_name
                        ].iloc[0]
                        original_nama = match_row[nama_col]
                        nim_val = match_row[nim_col]

                        invalid_data.append(
                            {
                                "Class": prakt.value,
                                "Row": "-",
                                "NIM": nim_val,
                                "Nama": original_nama,
                                "Module": "N/A",
                                "Parameter": "Extra Student (?)",
                                "Value": "Not in original file",
                            }
                        )
                except StopIteration:
                    print(
                        f"⚠️ Could not find Nama column in Original Data for {prakt.value}. Skipping roster check."
                    )

            for idx, row in df.iterrows():
                nim = row[nim_col]
                nama = row[nama_col]

                if pd.isna(nim) and pd.isna(nama):
                    continue

                for module in selected_modules:
                    try:
                        presensi = row.get((module, "Presensi"), "")
                        tp = row.get((module, "TP"), 0)
                        ta = row.get((module, "TA"), 0)
                        d = row.get((module, "D"), 0)
                        i = row.get((module, "I"), 0)

                        if self.is_empty(presensi):
                            invalid_data.append(
                                {
                                    "Class": prakt.value,
                                    "Row": int(str(idx)) + 1,
                                    "NIM": nim,
                                    "Nama": nama,
                                    "Module": module,
                                    "Parameter": "Presensi Belum Tercantum",
                                    "Value": presensi,
                                }
                            )
                            continue

                        if str(presensi).strip() == "Tidak Hadir" and all(
                            self.is_zero(x) or self.is_empty(x) for x in [ta, d, i]
                        ):
                            continue

                        for param, value in [
                            ("TP", tp),
                            ("TA", ta),
                            ("D", d),
                            ("I", i),
                        ]:
                            if not self.is_valid(param, value):
                                reason = ""
                                match param:
                                    case "TP":
                                        reason = (
                                            "Nilai Tugas Pendahuluan Invalid/Kosong"
                                        )
                                    case "TA":
                                        reason = (
                                            "Nilai Tugas Awal Invalid"
                                            if ta != 0
                                            else "Nilai Tugas Awal Invalid/Kosong"
                                        )
                                    case "D":
                                        reason = "Nilai Jurnal Invalid"
                                    case "I":
                                        reason = "Nilai Mandiri/Tugas Akhir Invalid"

                                invalid_data.append(
                                    {
                                        "Class": prakt.value,
                                        "Row": int(str(idx)) + 1,
                                        "NIM": nim,
                                        "Nama": nama,
                                        "Module": module,
                                        "Parameter": reason,
                                        "Value": value,
                                    }
                                )
                    except KeyError:
                        continue

            self.anomaly_data[prakt] = pd.DataFrame(invalid_data)

        self.save_cache()

    def export(self, file_path: str):
        with pd.ExcelWriter(file_path) as writer:
            for prakt, df in self.anomaly_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=prakt.value, index=False)

    def get_original(self, praktikans: Prak):
        return self.original_data.get(praktikans, pd.DataFrame())

    def get_loaded(self, praktikans: Prak):
        return self.loaded_data.get(praktikans, pd.DataFrame())

    def get_anomaly(self, praktikans: Prak):
        return self.anomaly_data.get(praktikans, pd.DataFrame())

    def get_count_original(self) -> int:
        return sum(len(df) for df in self.original_data.values())

    def get_count_loaded(self) -> int:
        return sum(len(df) for df in self.loaded_data.values())

    def get_count_anomaly(self) -> int:
        return sum(len(df) for df in self.anomaly_data.values())

    def reset(self):
        self.original_data = {}
        self.loaded_data = {}
        self.anomaly_data = {}
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
