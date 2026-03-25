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

    def load_batch(self, type: str, file_paths: list):
        for path in file_paths:
            praktikans = self.categorize_file(path)
            df = pd.read_excel(path)

            match type:
                case "original":
                    if praktikans in self.original_data:
                        self.original_data[praktikans] = pd.concat(
                            [self.original_data[praktikans], df], ignore_index=True
                        )
                    else:
                        self.original_data[praktikans] = df
                case "loaded":
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

    def analyze(self):
        self.anomaly_data = {}
        for prakt, df in self.loaded_data.items():
            self.anomaly_data[prakt] = pd.DataFrame()
        self.save_cache()

    def export(self, file_path: str):
        with pd.ExcelWriter(file_path) as writer:
            for prakt, df in self.anomaly_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=prakt.value, index=False)

    def reset(self):
        # Reset all of the data
        self.original_data = {}
        self.loaded_data = {}
        self.anomaly_data = {}

        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
