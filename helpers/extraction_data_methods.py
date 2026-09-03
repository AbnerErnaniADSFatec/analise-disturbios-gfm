import json

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


def extract_bands_ts(samples, line, bands_to_select):
    ts_ = pd.DataFrame(json.loads(samples['time_series'][line]))
    bands_ = ["Index"] + bands_to_select
    ts_ = ts_[bands_]
    return ts_

def extract_bands(samples, bands):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(extract_bands_ts(samples_, row, bands).to_dict(orient="list"))
    return samples_

def get_band_description(band, bands_description):
    selected = {}
    for band_desc in bands_description:
        if band_desc['name'] == band:
            selected = band_desc
            break
    return selected
    
def normalize_ts(samples, line, bands_description):
    ts_ = pd.DataFrame(json.loads(samples['time_series'][line]))
    for column in ts_.columns:
        if column != "Index":
            band_desc = get_band_description(column, bands_description)
            scale = band_desc['scale']
            ts_[column] = ts_[column] * scale
    return ts_

def normalize_(samples, bands_description):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(normalize_ts(samples_, row, bands_description).to_dict(orient="list"))
    return samples_

def _set_NaN(value, missing_value):
    if value != missing_value:
        return value
    else:
        return None
    
def std_(X_):
    std = X_.std(axis=0)
    std[std == 0] = 1
    return std

def interpolate_ts(samples, line, bands_description):
    ts_ = pd.DataFrame(json.loads(samples['time_series'][line]))
    for column in ts_.columns:
        if column != "Index":
            band_desc = get_band_description(column, bands_description)
            scale = band_desc['scale']
            missing_value = band_desc['nodata'] * scale
            ts_[column] = ts_[column].apply(lambda x: _set_NaN(x, missing_value)).interpolate(
                method = 'linear',
                limit_direction = 'forward',
                order = 2
            )
    return ts_

def interpolate_single_ts(ts_, bands_description):
    for column in ts_.columns:
        if column != "Index":
            band_desc = get_band_description(column, bands_description)
            scale = band_desc['scale']
            missing_value = band_desc['nodata'] * scale
            ts_[column] = ts_[column].apply(lambda x: _set_NaN(x, missing_value)).interpolate(
                method = 'linear',
                limit_direction = 'forward',
                order = 2
            )
    return ts_

def interpolate_(samples, bands_description):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(interpolate_ts(samples_, row, bands_description).to_dict(orient="list"))
    return samples_

class SGolay:
    def __init__(self, window_size: int, polynomial_order: int, mode: str = "interp"):
        self.mode = mode
        if (window_size % 2) != 0:
            self.window_size = window_size
        else:
            raise Exception("Window size must be odd number!")
        if window_size > polynomial_order:
            self.polynomial_order = polynomial_order
        else:
            raise Exception("Window size must be higher than the polynomial order!")

    def apply(self, samples, line):
        ts_ = pd.DataFrame(json.loads(samples['time_series'][line]))
        return self.apply_ts(ts_)

    def apply_ts(self, ts_):
        for column in ts_.columns:
            if column != "Index":
                ts_[column] = savgol_filter(
                    ts_[column],
                    window_length=self.window_size,
                    polyorder=self.polynomial_order,
                    mode=self.mode
                )
        return ts_

def smooth_(samples, sgolay):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(sgolay.apply(samples_, row).to_dict(orient="list"))
    return samples_

def getAllClasses(samples):
    cores_classes = {
        "CORTE SELETIVO": "#FF694D",
        "VEGETACAO NATURAL FLORESTAL SECUNDARIA": "#00991A",
        "VEGETACAO NATURAL FLORESTAL PRIMARIA": "#70FF85",
    }
    classes = np.unique(samples["label"])
    return pd.DataFrame(
        {
            "class_name": classes,
            "index": list(range(len(classes))),
            "color": [cores_classes.get(c, "#808080") for c in classes],
        }
    )

def getClass(samples, index=-1, label=''):
    classes = getAllClasses(samples)
    if index >= 0:
        result = classes[index == classes["index"]]
    if len(label):
        result = classes[label == classes["class_name"]]
    result = result.reset_index(drop = True)
    return result

def extract_features(row_or_string):
    # Caso 1: Série temporal do Sentinel-2 (string JSON ou dict)
    if isinstance(row_or_string, (str, dict)):
        ts = (
            json.loads(row_or_string.replace('""', '"'))
            if isinstance(row_or_string, str)
            else row_or_string
        )
        all_features = [
            np.array(ts[k], dtype=float) for k in ts.keys() if k != "Index"
        ]
        return np.concatenate(all_features)

    # Caso 2: Linha de DataFrame/Series (AlphaEarth ou Tessera)
    if isinstance(row_or_string, (pd.Series, dict)):
        cols = list(row_or_string.keys())

        # Detecção AlphaEarth (A00 .. A63/A64)
        ae_cols = sorted(
            [c for c in cols if c.startswith("A") and c[1:].isdigit()]
        )
        if ae_cols:
            return np.array([float(row_or_string[c]) for c in ae_cols])

        # Detecção Tessera (T0 .. T127 ou T00 .. T127)
        tes_cols = sorted(
            [c for c in cols if c.startswith("T") and c[1:].isdigit()],
            key=lambda x: int(x[1:]),
        )
        if tes_cols:
            return np.array([float(row_or_string[c]) for c in tes_cols])

        # Caso seja uma linha que contenha a coluna 'time_series'
        if "time_series" in row_or_string:
            return extract_features(row_or_string["time_series"])

    raise ValueError(
        "Formato não reconhecido para extração de features (esperado JSON de série temporal, AlphaEarth ou Tessera)."
    )

### Método para codificar as labels
def encode_label(samples, label_):
    return int(getClass(samples, label = label_)['index'].iloc[0])

def one_hot(labels, num_classes):
    """Converte uma lista de índices inteiros em uma matriz/vetor one-hot."""
    return np.eye(num_classes)[labels]

def plot_dist(train, val, test):
    # Quantidade de amostras
    train_size = len(train)
    val_size = len(val)
    test_size = len(test)
    
    sizes = [train_size, val_size, test_size]
    labels = [
        f"Train ({train_size})",
        f"Validation ({val_size})",
        f"Test ({test_size})"
    ]
    plt.figure()
    plt.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90
    )
    plt.title("Dataset Split Proportions")
    plt.axis('equal')
    plt.show()

    return train_size, val_size, test_size
