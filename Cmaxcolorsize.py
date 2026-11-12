# -*- coding: utf-8 -*-
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

INPUT_FILE = "n13-24.xlsx"
OUTPUT_FILE = "Cmax.pdf"
N_VALUES = list(range(13, 25))
SHOW_XTICK_LABELS = True
POINT_SIZE = 35        # 细横线的大小
POINT_ALPHA = 0.90

df = pd.read_excel(INPUT_FILE)

# 去除列名两端可能存在的隐藏空格
df.columns = df.columns.str.strip()

def clean_category(category):
    if pd.isna(category):
        return "Unknown"
    return str(category).strip().upper().replace("-", "_").replace(" ", "")

df["Category"] = df["Category"].apply(clean_category)

def get_large_category(category):
    for prefix in ["III", "II", "IV", "I", "V"]:
        if category.startswith(prefix):
            return prefix
    return category

df["Large_Category"] = df["Category"].apply(get_large_category)
large_category_order = ["I", "II", "III", "IV", "V"]

def subcategory_sort_key(category):
    match = re.match(r"^([IV]+)", category)
    if match:
        main_part = match.group(1)
        roman_order = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        
        # 精确控制 Category I 内小分类的排序顺序：让 I_1/2 排在第三个
        if main_part == "I":
            i_order_mapping = {
                "I_1": 1,
                "I_2": 2,
                "I_1/2": 3,
                "I_1_2": 3
            }
            sub_weight = i_order_mapping.get(category, 99)
            return (roman_order.get(main_part, 99), sub_weight)
        
        # 精确控制 Category III 内小分类的排序顺序
        if main_part == "III":
            iii_order_mapping = {
                "III_1": 1,
                "III_2": 2,
                "III_1/2": 3,
                "III_1_2": 3,
                "III_3": 4
            }
            sub_weight = iii_order_mapping.get(category, 99)
            return (roman_order.get(main_part, 99), sub_weight)
        
        # 其他大分类保持默认解析规则
        sub_match = re.match(r"^[IV]+_(\d+)", category)
        sub_num = int(sub_match.group(1)) if sub_match else 0
        return (roman_order.get(main_part, 99), sub_num)
    return (99, 99)

# ==========================================
# 严格按每个小分类内部 Rule # 升序排序
# ==========================================
reordered_df_list = []
for large_cat in large_category_order:
    large_df = df[df["Large_Category"] == large_cat].copy()
    if large_df.empty:
        continue
    subcategories = sorted(large_df["Category"].unique(), key=subcategory_sort_key)
    for subcat in subcategories:
        sub_df = large_df[large_df["Category"] == subcat].copy()
        sub_df = sub_df.sort_values(by="Rule #", ascending=True)
        reordered_df_list.append(sub_df)

if reordered_df_list:
    df = pd.concat(reordered_df_list, ignore_index=True)

def extract_max_cycle(cycle_structure):
    if pd.isna(cycle_structure):
        return np.nan
    cycles = re.findall(r"C\s*=\s*(\d+)", str(cycle_structure))
    return max([int(c) for c in cycles]) if cycles else np.nan

results = []
for idx, row in df.iterrows():
    rule, category, large_category = row["Rule #"], row["Category"], row["Large_Category"]
    for n in N_VALUES:
        max_cycle = extract_max_cycle(row[f"Cycle Structure (n={n})"])
        value = np.log(max_cycle / n) if (not pd.isna(max_cycle) and max_cycle > 0) else np.nan
        results.append({
            "Order": idx, "Rule": rule, "Large Category": large_category,
            "Category": category, "n": n, "Max Cycle": max_cycle,
            "Max Cycle / n": (max_cycle / n if not pd.isna(max_cycle) else np.nan),
            "ln(Max Cycle / n)": value
        })

result_df = pd.DataFrame(results)
rule_order = df["Rule #"].tolist()
x_positions = np.arange(len(rule_order))
valid_df = result_df.dropna(subset=["ln(Max Cycle / n)"]).copy()
valid_df["y_round"] = valid_df["ln(Max Cycle / n)"].round(6)

mult_counts = valid_df.groupby(["Rule", "y_round"]).size().reset_index(name="Multiplicity")
plot_data = pd.merge(valid_df, mult_counts, on=["Rule", "y_round"])

# 按要求严格设定：紫、蓝、绿、黄、红（每种分深浅），共12个节点对应 13~24
colors_purple_blue_green_yellow_red = [
    "#1f0954",  # 13: 深紫
    "#8A2BE2",  # 14: 浅紫
    "#0e87cc",  # 15: 深蓝
    "#85d0fc",  # 16: 浅蓝
    "#006400",  # 17: 深绿
    "#32CD32",  # 18: 浅绿
    "#B8860B",  # 19: 深黄 (暗金黄)
    "#FFD700",  # 20: 浅黄 (明金黄)
    "#FF8C00",  # 21: 深橙黄
    "#Fdc1c5",  # 22: 浅红橙
    "#B22222",  # 23: 深红
    "#FF0000"   # 24: 鲜红
]

cmap = LinearSegmentedColormap.from_list("purple_blue_green_yellow_red", colors_purple_blue_green_yellow_red)
n_colors = {
    n: cmap(i / (len(N_VALUES) - 1)) for i, n in enumerate(N_VALUES)
}

fig, ax = plt.subplots(figsize=(20, 8))

category_regions = []
present_large_categories = [cat for cat in large_category_order if cat in set(df["Large_Category"])]
for large_cat in present_large_categories:
    indices = [i for i, row in df.iterrows() if row["Large_Category"] == large_cat]
    if indices:
        category_regions.append((large_cat, min(indices), max(indices)))

class_background_colors = {
    "I": "#E2EEF3", 
    "II": "#E6F2E2", 
    "III": "#EFE6F6", 
    "IV": "#F6EFE6", 
    "V": "#D4D4D4"
}
class_text_colors = {
    "I": "#1F4048", 
    "II": "#2A3824", 
    "III": "#362A43", 
    "IV": "#453424", 
    "V": "#243745"
}

# ==========================================
# 【背景颜色控制区】：绘制大分类的背景色块
# ==========================================
for large_cat, left, right in category_regions:
    ax.axvspan(left - 0.5, right + 0.5, color=class_background_colors.get(large_cat, "#E2E2E2"), alpha=0.45, zorder=0)

# 绘制细横线
for n in N_VALUES:
    n_df = plot_data[plot_data["n"] == n]
    if n_df.empty:
        continue
    x_indices = [rule_order.index(r) for r in n_df["Rule"]]
    ax.scatter(
        x_indices, n_df["y_round"],
        marker="_", s=POINT_SIZE, color=n_colors[n], alpha=POINT_ALPHA,
        linewidths=1.3, zorder=3
    )

handles = [
    Line2D([0], [0], marker="_", color=n_colors[n],
           linewidth=2.0, markersize=8, label=str(n))
    for n in N_VALUES
]

legend = ax.legend(
    handles=handles, title=r"System size $n$", ncol=2, loc="upper left",
    bbox_to_anchor=(0.003, 0.975), frameon=True, fancybox=True, framealpha=1,
    facecolor="white", edgecolor="#D8DDE2", borderpad=0.75, labelspacing=0.55,
    columnspacing=1.0, handletextpad=0.5, fontsize=15, title_fontsize=10.5
)
legend.get_frame().set_linewidth(0.8)

ax.axhline(y=0, color="#555555", linestyle="-", linewidth=1.2, alpha=0.8, zorder=2)
ax.set_xlim(-1, len(rule_order))
ax.set_xticks(x_positions)

if SHOW_XTICK_LABELS:
    ax.set_xticklabels([str(r) for r in rule_order], rotation=90, ha="center", fontsize=8)
else:
    ax.set_xticklabels([])

ax.set_xlabel("ECA Rules", fontsize=20)
ax.set_ylabel(r"$\ln(C_{\max}(n)/n)$", fontsize=20)
ax.grid(axis="y", linestyle="--", color="#BFC5CA", alpha=0.32, linewidth=0.7, zorder=1)

# ==========================================
# 所有大分类标签（已注释掉 bbox 边框，去掉注释即可显现）
# ==========================================
y_class_offset = 1.180

for idx, (large_cat, left, right) in enumerate(category_regions):
    center = (left + right) / 2.0
    if left > 0:
        ax.axvline(left - 0.5, color='black',
                   linestyle="-", alpha=0.75, linewidth=1.2, zorder=1)
    
    ax.text(
        center, y_class_offset, f"Category {large_cat}", transform=ax.get_xaxis_transform(),
        ha="center", va="center", fontsize=18, fontweight="bold",
        color=class_text_colors.get(large_cat, "#333333"),
        # bbox=dict(boxstyle="round,pad=0.40", facecolor="white", edgecolor="black", linewidth=1.2, alpha=0.95),  # <-- 去掉行首 # 即可显示边框
        clip_on=False
    )

# ==========================================
# 小分类标签（已注释掉 bbox 边框，去掉注释即可显现）
# ==========================================
y_sub_offset = 1.030

for i, (subcat, sub_df) in enumerate(df.groupby("Category", sort=False)):
    indices = sub_df.index.tolist()
    if indices:
        left, right = min(indices), max(indices)
        center = (left + right) / 2.0
        if left > 0:
            ax.axvline(left - 0.5, color="#6C757D", linestyle="--", alpha=1, linewidth=0.9, zorder=1)
        
        ax.text(
            center, y_sub_offset, subcat, transform=ax.get_xaxis_transform(),
            ha="center", va="center", fontsize=15, fontweight="bold", color="#111111",
            # bbox=dict(boxstyle="round,pad=0.30", facecolor="white", edgecolor="black", linewidth=1.1, alpha=1),  # <-- 去掉行首 # 即可显示边框
            clip_on=False
        )

ax.set_title(r"Maximum Cycle Length", fontsize=22, fontweight="normal", pad=85)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#AEB4B8")
ax.spines["bottom"].set_color("#AEB4B8")

plt.subplots_adjust(left=0.06, right=0.98, bottom=0.15, top=0.66)
plt.savefig(OUTPUT_FILE, format="pdf", dpi=300, bbox_inches="tight")
print("PDF created successfully without text boxes!")

plt.show()