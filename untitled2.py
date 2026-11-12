# -*- coding: utf-8 -*-
import re
import pandas as pd
from pathlib import Path
from fractions import Fraction

INPUT_FILE = Path(r"D:\新建文件夹\code\n13-24.xlsx")
OUTPUT_DIR = INPUT_FILE.parent / "Category_II_Verification"
OUTPUT_EXCEL = OUTPUT_DIR / "Category_II_Integrated_Spectra_Metrics.xlsx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
n_values = list(range(13, 25))

# 规则家族分类
II1_RULES = {4, 12, 13, 36, 44, 72, 76, 77, 78, 104, 132, 140, 164, 172, 200, 204, 232}
II2_AND_108_RULES = {108, 1, 5, 19, 23, 28, 29, 33, 37, 50, 51, 156, 178}
RULE_62 = {62}
TARGET_RULES = list(II1_RULES | II2_AND_108_RULES | RULE_62)

def get_dominant_angles(rule_num: int):
    """返回每类规则对应的 dominant eigenvalues 角度集合 (Fraction in [0, 1))"""
    if rule_num in II1_RULES:
        return {Fraction(0, 1)}  # {1}
    elif rule_num in II2_AND_108_RULES:
        return {Fraction(0, 1), Fraction(1, 2)}  # {1, -1}
    elif rule_num in RULE_62:
        # 3-rd roots of unity: {1, e^{2pi i/3}, e^{4pi i/3}}
        return {Fraction(0, 1), Fraction(1, 3), Fraction(2, 3)}
    raise ValueError(f"Unknown rule: {rule_num}")

def get_family_label(rule_num: int) -> str:
    if rule_num in II1_RULES:
        return "II1"
    elif rule_num == 108:
        return "Rule 108"
    elif rule_num == 62:
        return "Rule 62"
    return "II2"

def parse_cycles_safe(val):
    if pd.isna(val) or not (text := str(val).strip()):
        return {}
    res = {}
    for C, x in re.findall(r"C\s*=\s*(\d+)\s*\(\s*x\s*(\d+)\s*\)", text, flags=re.IGNORECASE):
        C, x = int(C), int(x)
        if C > 0 and x > 0:
            res[C] = res.get(C, 0) + x
    return res

def format_eigenvalue_position(angle):
    if angle == 0:
        return "1"
    if angle == Fraction(1, 2):
        return "-1"
    coef = 2 * angle
    if coef.denominator == 1:
        return f"{coef.numerator}*pi"
    if coef.numerator == 1:
        return f"pi/{coef.denominator}"
    return f"{coef.numerator}*pi/{coef.denominator}"

def get_unit_circle_spectra_dict(cycles):
    spectra = {}
    for C, m in cycles.items():
        if C > 0 and m > 0:
            for k in range(C):
                angle = Fraction(k, C) % 1
                spectra[angle] = spectra.get(angle, 0) + m
    return spectra

df = pd.read_excel(INPUT_FILE)
df.columns = [str(c).strip() for c in df.columns]
rule_col = next((c for c in df.columns if re.search(r"rule\s*#", c, flags=re.IGNORECASE) or c.strip().lower() == "rule"), None)
if not rule_col:
    raise ValueError("Cannot find Rule # column.")

cycle_columns = {int(m.group(1)): c for c in df.columns if (m := re.search(r"cycle\s*structure\s*\(\s*n\s*=\s*(\d+)\s*\)", c, flags=re.IGNORECASE))}
if missing := [n for n in n_values if n not in cycle_columns]:
    raise ValueError(f"Missing n={missing}")

df["_rule_num"] = pd.to_numeric(df[rule_col], errors="coerce")
category_ii_df = df[df["_rule_num"].isin(TARGET_RULES)].copy()

split_rows, metrics_rows, cycle_check_rows = [], [], []

for _, row in category_ii_df.iterrows():
    rule_name = row[rule_col]
    rule_num = int(row["_rule_num"])
    family_label = get_family_label(rule_num)
    dom_angles = get_dominant_angles(rule_num)

    for n in n_values:
        cycles = parse_cycles_safe(row[cycle_columns[n]])
        exact_spectra = get_unit_circle_spectra_dict(cycles)
        
        formatted_spectra = {}
        for angle, m in exact_spectra.items():
            pos = format_eigenvalue_position(angle)
            formatted_spectra[pos] = formatted_spectra.get(pos, 0) + m

        tot_cycles = sum(cycles.values())
        tot_states = sum(C * x for C, x in cycles.items())
        tot_spectral = sum(exact_spectra.values())
        
        cycle_check_rows.append({
            "Family": family_label,
            "Rule Name": rule_name,
            "n": n,
            "Total Number of Cycles": tot_cycles,
            "Total Number of States": tot_states,
            "Total Spectral Multiplicity": tot_spectral,
            "Cycle Count Check": "PASS" if tot_spectral == tot_states else "FAIL"
        })

        if formatted_spectra:
            for pos_str, mult in formatted_spectra.items():
                split_rows.append({
                    "Family": family_label,
                    "Rule Name": rule_name,
                    "n": n,
                    "Unit Circle Position": pos_str,
                    "Multiplicity": mult
                })
        else:
            split_rows.append({
                "Family": family_label,
                "Rule Name": rule_name,
                "n": n,
                "Unit Circle Position": "None",
                "Multiplicity": 0
            })

        # 严格按照定义提取 Dominant 与 Secondary 特征值重度
        # 注意：只从当前 n 实际存在的谱 (exact_spectra) 中提取 dominant 重度
        dom_mults = [exact_spectra[a] for a in dom_angles if a in exact_spectra]
        sec_mults = [m for a, m in exact_spectra.items() if a not in dom_angles]

        min_dom_mult = min(dom_mults) if dom_mults else 0
        max_sec_mult = max(sec_mults) if sec_mults else 0
        has_secondary = 1 if sec_mults else 0

        # Ratio = largest multiplicity of secondary / smallest multiplicity of dominant
        ratio = (max_sec_mult / min_dom_mult) if (has_secondary and min_dom_mult > 0) else 0

        metrics_rows.append({
            "Family": family_label,
            "Rule Name": rule_name,
            "n": n,
            "Multiplicity_1": exact_spectra.get(Fraction(0, 1), 0),
            "Multiplicity_-1": exact_spectra.get(Fraction(1, 2), 0),
            "Multiplicity_e^(2pi/3)": exact_spectra.get(Fraction(1, 3), 0),
            "Has_Secondary_Check": has_secondary,
            "Min_Dominant_Multiplicity": min_dom_mult,
            "Max_Secondary_Multiplicity": max_sec_mult,
            "Ratio_MaxSec_to_MinDom": ratio
        })

df_metrics = pd.DataFrame(metrics_rows)
with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
    pd.DataFrame(split_rows).to_excel(writer, sheet_name="Unit Circle Spectra Split", index=False)
    df_metrics.to_excel(writer, sheet_name="All Metrics Summary", index=False)
    df_metrics[["Family", "Rule Name", "n", "Min_Dominant_Multiplicity", "Max_Secondary_Multiplicity", "Ratio_MaxSec_to_MinDom"]].to_excel(writer, sheet_name="Ratio MaxSec to MinDom", index=False)
    pd.DataFrame(cycle_check_rows).to_excel(writer, sheet_name="Cycle Count Verification", index=False)

print("done")