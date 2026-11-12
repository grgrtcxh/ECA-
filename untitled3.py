import matplotlib.pyplot as plt
import pandas as pd

# 1. 调色板定义（共 12 个颜色，分别对应 n = 13 到 24）
distinct_palette = [
    "#1f0954",
    "#8A2BE2",
    "#0e87cc",
    "#85d0fc",
    "#006400",
    "#32CD32",
    "#B8860B",
    "#FFD700",
    "#FF8C00",
    "#Fdc1c5",
    "#B22222",
    "#FF0000",
]

# 假设 n 从 13 到 24
n_values = list(range(13, 25))
color_map = dict(zip(n_values, distinct_palette))

# 2. 读取表格数据 (使用原始字符串 r'' 防止 Windows 路径下的转义符报错)
df = pd.read_excel(r"D:\新建文件夹\code\zhijiehuatu.xlsx")

# 假设表格结构：
# 第一列为 Rule (X轴)
# 第二列为 n 值
# 最后一列为具体的数值 (Y轴)
x_col = df.columns[0]  # 第一列：Rule
n_col = df.columns[1]  # 第二列：n 值
y_col = df.columns[-1]  # 最后一列：数值

# 获取所有唯一的 Rule 顺序并排序
rules = sorted(df[x_col].dropna().unique())
x_positions = {rule: i for i, rule in enumerate(rules)}

# 3. 找出“整列/所有 n 对应的值全为 0”的 Rule 集合
rule_all_zeros = []
for r in rules:
    sub = df[df[x_col] == r]
    # 如果该 rule 对应所有行的 y_col 的值全为 0（或者最大值等于0）
    if not sub.empty and (sub[y_col] == 0).all():
        rule_all_zeros.append(r)

# 4. 创建图表
fig, ax = plt.subplots(figsize=(16, 7), dpi=300)

# 5. 先绘制全为 0 的 Rule 在 X 轴位置上的浅灰色交叉点
if rule_all_zeros:
    zero_x_coords = [x_positions[r] for r in rule_all_zeros if r in x_positions]
    # Y 轴可以放在 0 的位置，或者靠近轴底部的微小偏移处
    zero_y_vals = [0] * len(zero_x_coords)

    ax.scatter(
        zero_x_coords,
        zero_y_vals,
        color="#C0C0C0",  # 更浅的灰色
        marker="x",
        s=90,
        linewidths=1.2,
        zorder=3,  # 确保显示在网格之上
    )

# 6. 遍历绘制其他正常的 n 的数据
for n in n_values:
    sub_df = df[df[n_col] == n]
    if sub_df.empty:
        continue

    # 排除掉那些本身就全为 0 的 rule，只画正常有数值的数据
    valid_sub = sub_df[~sub_df[x_col].isin(rule_all_zeros)]
    if valid_sub.empty:
        continue

    x_coords = [x_positions[r] for r in valid_sub[x_col] if r in x_positions]
    y_vals = valid_sub[y_col].loc[valid_sub[x_col].isin(x_positions)]

    ax.scatter(
        x_coords,
        y_vals,
        label=f"n = {n}",
        color=color_map[n],
        marker="_",
        s=450,
        linewidths=3.5,
    )

# 7. 图形样式与细节调整
ax.set_title(
    "Category II: Cycle Multiplicity Ratios (n = 13 to 24)",
    fontsize=20,
    pad=15,
)
ax.set_xlabel("Elementary Cellular Automaton Rule", fontsize=15, labelpad=8)
ax.set_ylabel("Secondary Multiplicity / Dominant  Multiplicity", fontsize=15)

# 显式设置 X 轴刻度
ax.set_xticks(range(len(rules)))
ax.set_xticklabels([str(r) for r in rules], rotation=45, ha="right", fontsize=11)
ax.set_xlim(-0.8, len(rules) - 0.2)

# 网格线与图例
ax.grid(axis="y", linestyle="--", alpha=0.35)
ax.set_axisbelow(True)

# 图例设置（多列置于左上方，不包含 0 的图例）
ax.legend(ncol=4, loc="upper left", frameon=True, fontsize=18, handlelength=1.5)

plt.tight_layout()

# 8. 保存为 PDF 文件
output_filename = "Cycle Multiplicity Ratios.pdf"
plt.savefig(output_filename, format="pdf", dpi=300)
print(f"图表已成功保存至: {output_filename}")

plt.show()