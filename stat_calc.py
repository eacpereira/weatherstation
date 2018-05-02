#!/usr/bin/env python
import scipy

def compute_least_squares(data):
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(data, range(1,61))

    return r_value, p_value


def regression_info(data):

    r_value, p_value = compute_least_squares(data)

    regression_info = {}

    p_data = dict()
    p_data["value"] = p_value
    if p_value <= 0.045:
        p_data["evidence"] = "strong"
        p_data["evidence_symbol"] = "◎"
    elif 0.045 < p_value < 0.055:
        p_data["evidence"] = "uncertain"
        p_data["evidence_symbol"] = "∼"
    elif p_value >= 0.055:
        p_data["evidence"] = "weak"
        p_data["evidence_symbol"] = "🗙"
    else:
        p_data["evidence"] = "unknown"
        p_data["evidence_symbol"] = "?"

    regression_info["p-value"] = p_data

    r_data = dict()
    r_data["value"] = r_value
    if r_value == 1:
        r_data["relationship"] = "rising straight up"
        r_data["relationship_symbol"] = "⤒"
    elif 0.7 <= r_value < 1:
        r_data["relationship"] = "rising strongly"
        r_data["relationship_symbol"] = "↑↑↑"
    elif 0.5 <= r_value < 0.7:
        r_data["relationship"] = "rising moderately"
        r_data["relationship_symbol"] = "↑↑"
    elif 0.3 < r_value < 0.5:
        r_data["relationship"] = "rising weakly"
        r_data["relationship_symbol"] = "↑"
    elif -0.3 <= r_value < 0.-0.3 and r_value != 0:
        r_data["relationship"] = "wavering"
        r_data["relationship_symbol"] = "⇝"
    elif r_value == 0:
        r_data["relationship"] = "unchanging"
        r_data["relationship_symbol"] = "→"
    elif -0.3 < r_value < -0.5:
        r_data["relationship"] = "falling weakly"
        r_data["relationship_symbol"] = "↓"
    elif 0.5 <= r_value < 0.7:
        r_data["relationship"] = "falling moderately"
        r_data["relationship_symbol"] = "↓↓"
    elif -0.7 <= r_value < -1:
        r_data["relationship"] = "falling strongly"
        r_data["relationship_symbol"] = "↓↓↓"
    elif r_value == -1:
        r_data["relationship"] = "falling straight down"
        r_data["relationship_symbol"] = "⤓"
    else:
        r_data["relationship"] = "unknown"
        r_data["relationship_symbol"] = "⟳"

    regression_info["r-value"] = r_data

    return regression_info
