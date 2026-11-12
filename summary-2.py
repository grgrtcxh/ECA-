# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 14:39:15 2026

@author: zqy
"""

import numpy as np
from itertools import product
import networkx as nx
from collections import Counter

# ==================================================
# 参数设置
# =================================================
rule_number = 88
boundary_type = 'periodic' #  或 'fixed''fixed' 
fixed_values = (0, 1) 

# 设置需要遍历的系统尺寸 n (从 3 到 15)
n_range =range(4, 5)

# 用于存储所有 n 的宏观统计数据，供后期如果需要导出 txt 时使用
global_summary_data = {}

# ==================================================
# ECA 局部规则与状态转移核心函数
# ==================================================
def eca_rule(left, center, right, rule):
    pattern = (left << 2) | (center << 1) | right
    return (rule >> pattern) & 1

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
# 核心循环：计算并输出 n = 3 到 15 的结果
# ==================================================
for n in n_range:
    # 1. 生成状态空间
    S = {"".join(map(str, s)) for s in product([0, 1], repeat=n)}
    
    # 2. 计算转移映射并构建网络图
    F = {}
    G = nx.DiGraph()
    G.add_nodes_from(S)
    for node_str in S:
        state_tuple = tuple(map(int, node_str))
        nxt_tuple = next_state(state_tuple, rule_number, boundary_type, fixed_values)
        nxt_str = "".join(map(str, nxt_tuple))
        F[node_str] = nxt_str
        G.add_edge(node_str, nxt_str)
        
    # 3. 拓扑结构剥离
    S_current = set(S)
    while True:
        S_next = {F[x] for x in S_current}
        if S_next == S_current:
            break
        S_current = S_next
    S_core = S_current  
    
    garden_of_eden = {node for node in S if G.in_degree(node) == 0}
    all_non_core = S - S_core
    confluence_relay = {node for node in all_non_core if G.in_degree(node) > 0 and G.out_degree(node) > 0}
    pure_leaf_states = all_non_core - garden_of_eden - confluence_relay
    
    # 4. 计算独立组件与循环
    components = list(nx.weakly_connected_components(G))
    cycle_info = []
    
    for comp in components:
        subG = G.subgraph(comp)
        comp_cycles = list(nx.simple_cycles(subG))
        comp_cycle_nodes = comp_cycles[0] if comp_cycles else []
        T = len(comp_cycle_nodes)
        
        if T > 0:
            cycle_info.append(T)
            
    # 合并统计
    aggregated_cycles = Counter(cycle_info)
    
    # 暂存数据供后期（被注释的）TXT 部分使用
    global_summary_data[n] = {
        'S_size': len(S), 'S_core': len(S_core), 'cycle_info_len': len(cycle_info),
        'aggregated_cycles': aggregated_cycles, 'garden_of_eden': len(garden_of_eden),
        'confluence_relay': len(confluence_relay)
    }
    
    # ==================================================
    # 标准控制台输出 (移除了第3部分特征值分类与校验)
    # ==================================================
    print("=" * 65)
    print(f"Global State Report for n = {n} ({boundary_type.upper()} boundary)")
    print("=" * 65)
    print(f"Total State Space Size (2^n): {len(S)}")
    print(f"  1. Attractor Core States  : {len(S_core)}")
    print(f"     Total Cycles : {len(cycle_info)}")
    for c_len, count in sorted(aggregated_cycles.items()):
        print(f"     [elements on cycle]: {c_len:2d} states  |  [count]: x{count}")
        
    print(f"  2. Garden of Eden States : {len(garden_of_eden)}")
    print(f"  3. Transient States      : {len(confluence_relay)}")
    print("=" * 65 + "\n\n")


# =============================================================================
# 以下为被注释掉的【TXT自动化输出文档模块】
# 若要启用，请删除前后的三个单引号 (''') 即可
# =============================================================================
'''
# ==================================================
# 7. 自动化输出文档 Part (批量写入外部文件报告)
# ==================================================
txt_filename = f"ECA_Rule{rule_number}_Batch_Analysis_Report.txt"

with open(txt_filename, "w", encoding="utf-8") as f:
    f.write("=" * 65 + "\n")
    f.write(f"Batch Global Spectral and Topological Analysis (n=3 to 15)\n")
    f.write("=" * 65 + "\n")
    f.write(f"Rule Number                  : {rule_number}\n")
    f.write(f"Boundary Type                : {boundary_type.upper()}\n")
    f.write("=" * 65 + "\n\n")
    
    for n, data in global_summary_data.items():
        f.write("=" * 65 + "\n")
        f.write(f"Global State Report for n = {n} ({boundary_type.upper()} boundary)\n")
        f.write("=" * 65 + "\n")
        f.write(f"Total State Space Size (2^n): {data['S_size']}\n")
        f.write(f"  1. Attractor Core States  : {data['S_core']}\n")
        f.write(f"     Total Cycles : {data['cycle_info_len']}\n")
        for c_len, count in sorted(data['aggregated_cycles'].items()):
            f.write(f"     [elements on cycle]: {c_len:2d} states  |  [count]: x{count}\n")
        f.write(f"  2. Garden of Eden States : {data['garden_of_eden']}\n")
        f.write(f"  3. Transient States      : {data['confluence_relay']}\n")
        f.write("=" * 65 + "\n\n\n")

print(f"[TXT Export] Batch data (n=3~15) successfully saved to: '{txt_filename}'")
'''