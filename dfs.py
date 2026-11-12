# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 22:05:00 2026
@author: zqy
"""

from itertools import product
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# ==================================================
# Parameters (参数设置)
# ==================================================
n = 4
rule_number = 62

# Boundary condition options: 'periodic' or 'fixed'
boundary_type = 'periodic'  # 'fixed'

# If boundary_type is 'fixed', choose from: (0,0), (0,1), (1,0), (1,1)
fixed_values = (1, 1)  

# ==================================================
# ECA Rule (基本元胞自动机局部规则)
# ==================================================
def eca_rule(left, center, right, rule):
    pattern = (left << 2) | (center << 1) | right
    return (rule >> pattern) & 1

# ==================================================
# Next state with Optional Boundaries (计算下一状态)
# ==================================================
def next_state(state, rule, b_type='periodic', f_vals=(0, 0)):
    length = len(state)
    new_state = []
    for i in range(length):
        if b_type == 'periodic':
            left = state[(i - 1) % length]
            right = state[(i + 1) % length]
        elif b_type == 'fixed':
            left = f_vals[0] if i == 0 else state[i - 1]
            right = f_vals[1] if i == length - 1 else state[i + 1]
        
        center = state[i]
        new_state.append(eca_rule(left, center, right, rule))
    return tuple(new_state)

# ==================================================
# 1. Output Local Rule Table (输出局部规则表)
# ==================================================
print("=" * 55)
print(f"1. Local Rule Table (Rule {rule_number})")
print("=" * 55)
for p in range(7, -1, -1):
    left = (p >> 2) & 1
    center = (p >> 1) & 1
    right = p & 1
    res = eca_rule(left, center, right, rule_number)
    print(f"{left}{center}{right} --> {res}")

# ==================================================
# 2. Pure Set Algebra & Topology Analysis (非矩阵集合代数与拓扑分析)
# ==================================================
S = {"".join(map(str, s)) for s in product([0, 1], repeat=n)}

F = {}
for node_str in S:
    state_tuple = tuple(map(int, node_str))
    nxt_tuple = next_state(state_tuple, rule_number, boundary_type, fixed_values)
    F[node_str] = "".join(map(str, nxt_tuple))

F_S = {F[x] for x in S}
garden_of_eden = S - F_S  

S_current = set(S)
while True:
    S_next = {F[x] for x in S_current}
    if S_next == S_current:
        break
    S_current = S_next
S_core = S_current  

total_transients = S - S_core
transient_non_eden = total_transients - garden_of_eden  

# ==================================================
# 3. Print Non-Matrix Analysis Results (输出非矩阵分析结果)
# ==================================================
print("\n" + "=" * 55)
print(f"2. Global State Algebra Analysis ({boundary_type.upper()} boundary)")
if boundary_type == 'fixed':
    print(f"    Fixed boundary values: {fixed_values}")
print("=" * 55)
print(f"Total State Space Size (S)             : {len(S)}")
print(f"Total Transient States (λ = 0 equiv)   : {len(total_transients)}")
print(f"    Garden of Eden States (m=0): {len(garden_of_eden)} -> {sorted(list(garden_of_eden))}")
print(f"    Transient (m>=1): {len(transient_non_eden)} -> {sorted(list(transient_non_eden))}")
print(f"Total Attractor Cycle States           : {len(S_core)} -> {sorted(list(S_core))}")

# ==================================================
# 4. Graph Construction & Basin Breakdown (构建网络图与分量细化)
# ==================================================
print("\n" + "=" * 55)
print("3. Network Topology & Basin Breakdown")
print("=" * 55)

G = nx.DiGraph()
G.add_nodes_from(S)
for src, tgt in F.items():
    G.add_edge(src, tgt)

components = list(nx.weakly_connected_components(G))
print(f"Total Connected Components (Attractor Basins): {len(components)}\n")

all_cycle_nodes = set()
for comp in components:
    subG = G.subgraph(comp)
    cycles = list(nx.simple_cycles(subG))
    if cycles:
        all_cycle_nodes.update(cycles[0])

for idx, comp in enumerate(components, 1):
    subG = G.subgraph(comp)
    comp_eden = [node for node in comp if node in garden_of_eden]
    comp_transient = [node for node in comp if node in transient_non_eden]
    comp_cycles = list(nx.simple_cycles(subG))
    comp_cycle_nodes = comp_cycles[0] if comp_cycles else []
    
    print(f"--- Component #{idx} ---")
    print(f"  Total States in Basin              : {len(comp)}")
    print(f"  Garden of Eden States Count (m=0) : {len(comp_eden)} -> {sorted(comp_eden)}")
    print(f"  Transient Branch States Count     : {len(comp_transient)} -> {sorted(comp_transient)}")
    print(f"  Periodic Cycle States Count       : {len(comp_cycle_nodes)} -> {sorted(comp_cycle_nodes)}")
    print(f"  Cycle Path                        : {' -> '.join(comp_cycle_nodes) + ' -> ' + comp_cycle_nodes[0] if comp_cycle_nodes else 'None'}")
    print()

# ==================================================
# 5. Non-Overlapping Multi-Basin Layout Visualization (防重叠多盆地布局可视化)
# ==================================================
plt.figure(figsize=(11, 10))

# 【防重叠核心算法】为每个弱连通分量（Basin）独立计算局部布局，并进行网格平移排布
pos = {}
num_comps = len(components)
cols = math_cols = int(np.ceil(np.sqrt(num_comps))) # 动态计算网格列数

for idx, comp in enumerate(components):
    subG = G.subgraph(comp)
    # 使用局部弹簧布局，并大幅增大斥力参数 k，防止节点拥挤
    local_pos = nx.spring_layout(subG, seed=42, k=1.5, iterations=200)
    
    # 计算当前盆地在宏观画布中的偏移量
    row = idx // cols
    col = idx % cols
    offset_x = (col - cols / 2.0) * 3.5
    offset_y = (row - num_comps / cols / 2.0) * 3.5
    
    for node, coords in local_pos.items():
        pos[node] = (coords[0] + offset_x, coords[1] + offset_y)

# 动态为每个节点赋予分类颜色
node_colors = []
for node in G.nodes():
    if node in all_cycle_nodes:
        node_colors.append("#ff7f0e")  # 周期吸引子: 醒目橙色
    elif node in garden_of_eden:
        node_colors.append("#2ca02c")  # 伊甸园状态: 柔和绿色
    else:
        node_colors.append("#1f77b4")  # 过渡分支状态: 经典蓝色

# 绘制节点
nx.draw_networkx_nodes(
    G, pos, 
    node_size=1600,
    node_color=node_colors, 
    edgecolors="black", 
    linewidths=1.5
)

# 绘制状态文本标签
nx.draw_networkx_labels(
    G, pos, 
    font_size=10, 
    font_weight="bold", 
    font_color="white"
)

# 绘制有向箭头连线（优化弧度和边缘留白，防止箭头重叠戳进节点）
nx.draw_networkx_edges(
    G, pos, 
    arrows=True, 
    arrowstyle="-|>", 
    arrowsize=20, 
    edge_color="#555555", 
    width=1.5, 
    min_source_margin=24, 
    min_target_margin=24, 
    connectionstyle="arc3,rad=0.25"
)

# 添加图例 (Legend)
legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w', label='Attractor Cycle ', markerfacecolor='#ff7f0e', markersize=12, markeredgecolor='black'),
    plt.Line2D([0], [0], marker='o', color='w', label='Garden of Eden ', markerfacecolor='#2ca02c', markersize=12, markeredgecolor='black'),
    plt.Line2D([0], [0], marker='o', color='w', label='Transient State ', markerfacecolor='#1f77b4', markersize=12, markeredgecolor='black')
]
plt.legend(handles=legend_elements, loc="upper right", frameon=True, fontsize=10)

plt.title(f"Rule {rule_number}, n={n}", fontsize=14, fontweight='bold', pad=15)
plt.axis("off")
plt.tight_layout()
plt.show()