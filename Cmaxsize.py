# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 19:52:03 2026

@author: zqy
"""

# -*- coding: utf-8 -*-
"""
ECA Maximum Cycle Scaling Analysis (with Multiplicity)
======================================================
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def main():

    # ========================================================
    # 1. Parameters
    # ========================================================

    INPUT_FILE = "n13-24.xlsx"
    OUTPUT_FILE = "ECA_max_cycle_ln_scaling.png"

    N_VALUES = list(range(13, 25))
    JITTER = 0.0

    # --------------------------------------------------------
    # 控制参数
    # --------------------------------------------------------
    SHOW_XTICK_LABELS = True
    TARGET_RULES_TO_MOVE = [164, 172, 37, 62]  # 需要移到对应分类最右侧的 Rule

    # ========================================================
    # 2. Read Excel
    # ========================================================

    print("=" * 70)
    print("Reading Excel")
    print("=" * 70)

    df = pd.read_excel(INPUT_FILE)

    print(f"Loaded: {INPUT_FILE}")
    print(f"Rows: {len(df)}")

    # ========================================================
    # 3. Check required columns
    # ========================================================

    required_columns = ["Category", "Rule #"]

    for n in N_VALUES:
        required_columns.append(f"Cycle Structure (n={n})")

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(
            "Missing columns:\n" + "\n".join(missing)
        )

    # ========================================================
    # 4. Normalize Category
    # ========================================================

    def normalize_category(category):

        if pd.isna(category):
            return "Unknown"

        category = str(category).strip().upper()

        if category == "I":
            return "I"

        if category == "II":
            return "II"

        if category == "III":
            return "III"

        if category == "IV":
            return "IV"

        if category == "V":
            return "V"

        if re.match(r"^II[\-_ ]?[12]$", category):
            return "II"

        if "III" in category:
            return "III"

        if "IV" in category:
            return "IV"

        if "II" in category:
            return "II"

        if category.endswith("I"):
            return "I"

        if category.endswith("V"):
            return "V"

        return category

    df["Category_Group"] = df["Category"].apply(normalize_category)

    # ========================================================
    # 4.2 重新排列 DataFrame 行顺序：
    # 将 164, 172, 37, 62 移动到对应分类的最右侧
    # ========================================================

    categories_order = ["I", "II", "III", "IV", "V"]
    reordered_df_list = []

    for cat in categories_order:
        cat_df = df[df["Category_Group"] == cat]
        if cat_df.empty:
            continue

        normal_rules_df = cat_df[~cat_df["Rule #"].isin(TARGET_RULES_TO_MOVE)]
        moved_rules_df = cat_df[cat_df["Rule #"].isin(TARGET_RULES_TO_MOVE)]

        cat_reordered = pd.concat([normal_rules_df, moved_rules_df], ignore_index=True)
        reordered_df_list.append(cat_reordered)

    df = pd.concat(reordered_df_list, ignore_index=True)

    # ========================================================
    # 5. Extract maximum cycle length
    # ========================================================

    def extract_max_cycle(cycle_structure):

        if pd.isna(cycle_structure):
            return np.nan

        text = str(cycle_structure)

        cycles = re.findall(r"C\s*=\s*(\d+)", text)

        if not cycles:
            return np.nan

        cycles = [int(c) for c in cycles]

        return max(cycles)

    # ========================================================
    # 6. Calculate ln(max_cycle / n)
    # ========================================================

    results = []

    for idx, row in df.iterrows():

        rule = row["Rule #"]
        category = row["Category_Group"]

        for n in N_VALUES:

            column = f"Cycle Structure (n={n})"
            cycle_structure = row[column]
            max_cycle = extract_max_cycle(cycle_structure)

            if pd.isna(max_cycle) or max_cycle <= 0:
                value = np.nan
            else:
                ratio = max_cycle / n
                value = np.log(ratio)

            results.append(
                {
                    "Order": idx,
                    "Rule": rule,
                    "Category": category,
                    "n": n,
                    "Max Cycle": max_cycle,
                    "Max Cycle / n": (
                        max_cycle / n if not pd.isna(max_cycle) else np.nan
                    ),
                    "ln(Max Cycle / n)": value,
                }
            )

    result_df = pd.DataFrame(results)

    # ========================================================
    # 8. 颜色配置 (为 Category 分配颜色)
    # ========================================================

    categories = ["I", "II", "III", "IV", "V"]
    present_categories = [c for c in categories if c in set(result_df["Category"])]

    color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    category_colors = {
        category: color_cycle[i % len(color_cycle)]
        for i, category in enumerate(present_categories)
    }

    # ========================================================
    # 9. Create figure
    # ========================================================

    fig, ax = plt.subplots(figsize=(18, 7))

    # ========================================================
    # 10. 统计并绘制 Multiplicity (重数)
    # ========================================================

    rule_order = df["Rule #"].tolist()
    x_positions = np.arange(len(rule_order))

    # 剔除无效 NaN 数据
    valid_df = result_df.dropna(subset=["ln(Max Cycle / n)"]).copy()

    # 针对 Y 值做适当精度舍入，防止微小浮点误差影响统计
    valid_df["y_round"] = valid_df["ln(Max Cycle / n)"].round(6)

    # 按 Rule 和 Y 值分组，计算重数 (Multiplicity)
    grouped = (
        valid_df.groupby(["Rule", "Category", "y_round"])
        .size()
        .reset_index(name="Multiplicity")
    )

    # 基础圆点大小设定：base_size + multiplier * count
    BASE_SIZE = 20
    SIZE_FACTOR = 15

    for rule_index, rule in enumerate(rule_order):

        rule_data = grouped[grouped["Rule"] == rule]

        if len(rule_data) == 0:
            continue

        category = rule_data["Category"].iloc[0]
        color = category_colors.get(category, "gray")

        x = np.full(len(rule_data), rule_index, dtype=float)
        y = rule_data["y_round"].values
        multiplicity = rule_data["Multiplicity"].values

        # 根据重数计算每个散点的大小
        sizes = BASE_SIZE + (multiplicity - 1) * SIZE_FACTOR

        ax.scatter(
            x,
            y,
            s=sizes,
            color=color,
            alpha=0.6,
            edgecolors="black",  # 加上黑边以便更清晰区分重叠大小
            linewidths=0.6,
        )

    # ========================================================
    # 11. Highlight y = 0 Line
    # ========================================================

    ax.axhline(
        y=0,
        color="black",
        linestyle="-",
        linewidth=1.8,
        alpha=0.9,
        zorder=3,
    )

    # ========================================================
    # 12. X axis & Y axis
    # ========================================================

    ax.set_xlim(-1, len(rule_order))
    ax.set_xticks(x_positions)

    if SHOW_XTICK_LABELS:
        ax.set_xticklabels(
            [str(r) for r in rule_order],
            rotation=90,
            ha="center",
            fontsize=8,
        )
    else:
        ax.set_xticklabels([])

    ax.set_xlabel("ECA Rules", fontsize=13)
    ax.set_ylabel(r"$\ln(C_{\max}/n)$", fontsize=14)

    # ========================================================
    # 13. Grid
    # ========================================================

    ax.grid(axis="y", linestyle="--", alpha=0.35)

    # ========================================================
    # 14. Category indication
    # ========================================================

    for category in present_categories:

        indices = [
            i
            for i, rule in enumerate(rule_order)
            if normalize_category(df.iloc[i]["Category"]) == category
        ]

        if not indices:
            continue

        left = min(indices)
        right = max(indices)
        center = (left + right) / 2.0

        if left > 0:
            ax.axvline(left - 0.5, color="gray", linestyle=":", alpha=0.55)

        ax.text(
            center,
            1.015,
            category,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=13,
            fontweight="bold",
            color=category_colors[category],
        )

    # ========================================================
    # 15. Legends (图例：包含 Category 与 Multiplicity 规格)
    # ========================================================

    # Category 图例
    cat_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markersize=6,
            markerfacecolor=category_colors[c],
            markeredgecolor=category_colors[c],
            label=c,
        )
        for c in present_categories
    ]

    leg1 = ax.legend(
        handles=cat_handles,
        title="Category",
        loc="upper right",
        bbox_to_anchor=(1.12, 1.0),
        frameon=True,
    )
    ax.add_artist(leg1)  # 保持第一个图例

    # Multiplicity (重数大小) 图例
    sample_counts = [1, 3, 6, 12]  # 代表性重数示例
    size_handles = [
        ax.scatter(
            [],
            [],
            s=BASE_SIZE + (c - 1) * SIZE_FACTOR,
            color="gray",
            alpha=0.6,
            edgecolors="black",
            linewidths=0.6,
            label=f"{c} pts",
        )
        for c in sample_counts
    ]

    ax.legend(
        handles=size_handles,
        title="Multiplicity",
        loc="upper right",
        bbox_to_anchor=(1.12, 0.65),
        frameon=True,
    )

    # ========================================================
    # 16. Title & Layout
    # ========================================================

    ax.set_title(
        r"ECA Maximum Cycle Scaling: $\ln(C_{\max}/n)$",
        fontsize=15,
        pad=28,
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()