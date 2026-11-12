
# -*- coding: utf-8 -*-
"""
Optimized ECA Spectral Analysis
Functional-graph / Bitwise implementation
"""

import os
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

# ============================================================
# 1. 参数设置
# ============================================================
n = 17
rule_number = 43
num_fixed_bins = 500
chunk_size = 1_000_000

save_dir = "spectral_figures"
os.makedirs(save_dir, exist_ok=True)

print("=" * 75)
print(f"ECA SPECTRAL ANALYSIS | Rule = {rule_number} | n = {n} | bins = {num_fixed_bins}")
print("=" * 75)

start_total = time.time()

# ============================================================
# 2. 基本参数
# ============================================================
N = 1 << n
MASK = N - 1

print(f"Total states: 2^{n} = {N:,}")
print(f"Estimated state-transition memory: {N * 4 / 1024**2:.1f} MB\n")

# ============================================================
# 3. Bitwise ECA transition
# ============================================================
def eca_next_array(states, n, rule):
    mask = (1 << n) - 1
    left = ((states >> 1) | ((states & 1) << (n - 1))) & mask
    right = ((states << 1) | (states >> (n - 1))) & mask
    result = np.zeros_like(states, dtype=np.uint32)

    for p in range(8):
        L, C, R = (p >> 2) & 1, (p >> 1) & 1, p & 1
        mL = left if L else (~left) & mask
        mC = states if C else (~states) & mask
        mR = right if R else (~right) & mask
        
        pattern_mask = mL & mC & mR
        if (rule >> p) & 1:
            result |= pattern_mask

    return result

# ============================================================
# 4. Construct transition function
# ============================================================
print("Building transition function...")
t0 = time.time()

next_state = np.empty(N, dtype=np.uint32)

for start in range(0, N, chunk_size):
    end = min(start + chunk_size, N)
    states = np.arange(start, end, dtype=np.uint32)
    next_state[start:end] = eca_next_array(states, n, rule_number)
    
    if start % (chunk_size * 5) == 0:
        print(f"  Transition progress: {end / N * 100:6.2f}%")

print(f"Transition construction completed in {time.time() - t0:.2f} s")
print(f"Transition array memory: {next_state.nbytes / 1024**2:.1f} MB\n")

# ============================================================
# 5. Calculate indegree
# ============================================================
print("Calculating indegrees...")
t0 = time.time()

indegree = np.zeros(N, dtype=np.uint32)
indegree[:] = np.bincount(next_state, minlength=N)

print(f"Indegree calculation completed in {time.time() - t0:.2f} s\n")

# ============================================================
# 6. Functional graph cycle extraction
# ============================================================
print("Extracting cycle states...")
t0 = time.time()

queue = np.empty(N, dtype=np.uint32)
initial_zero = np.flatnonzero(indegree == 0).astype(np.uint32)
queue[:len(initial_zero)] = initial_zero

head = 0
tail = len(initial_zero)
removed_count = 0

while head < tail:
    state = queue[head]
    head += 1
    removed_count += 1
    nxt = next_state[state]
    indegree[nxt] -= 1
    
    if indegree[nxt] == 0:
        queue[tail] = nxt
        tail += 1

cycle_mask = (indegree > 0)
cycle_states = np.flatnonzero(cycle_mask)
unit_circle_count = len(cycle_states)

print(f"Cycle extraction completed in {time.time() - t0:.2f} s")
print(f"Cycle states: {unit_circle_count:,}")
print(f"Transient states: {N - unit_circle_count:,}")
print(f"Non-zero Mode Ratio: {unit_circle_count / N:.8f}\n")

# ============================================================
# 7. Extract cycle lengths
# ============================================================
print("Extracting cycle lengths...")
t0 = time.time()

visited = np.zeros(N, dtype=np.bool_)
cycle_lengths = []

for start_state in cycle_states:
    start_state = int(start_state)
    if visited[start_state]:
        continue

    current = start_state
    length = 0
    while not visited[current]:
        visited[current] = True
        length += 1
        current = int(next_state[current])
        
    cycle_lengths.append(length)

cycle_lengths = np.asarray(cycle_lengths, dtype=np.int64)

print(f"Cycle length extraction completed in {time.time() - t0:.2f} s")
print(f"Number of cycles: {len(cycle_lengths):,}")
print(f"Maximum cycle length: {cycle_lengths.max():,}\n")

# ============================================================
# 8. Construct spectral distribution
# ============================================================
print("Constructing spectral distribution...")

bin_edges = np.linspace(0, 2 * np.pi, num_fixed_bins + 1)
bin_counts = np.zeros(num_fixed_bins, dtype=np.int64)
lambda_one_count = len(cycle_lengths)

for T in cycle_lengths:
    T = int(T)
    if T > 1:
        phases = (np.arange(1, T, dtype=np.float64) / T) * 2 * np.pi
        indices = np.searchsorted(bin_edges, phases, side="right") - 1
        indices = np.clip(indices, 0, num_fixed_bins - 1)
        bin_counts += np.bincount(indices, minlength=num_fixed_bins)

# lambda = 1
bin_counts[-1] += lambda_one_count

# ============================================================
# 9. Bin centers & Ratios
# ============================================================
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
nonzero_mode_ratio = unit_circle_count / N
zero_mode_ratio = 1.0 - nonzero_mode_ratio
lambda_one_ratio = lambda_one_count / N

nonzero_mask = (bin_counts > 0)
plot_centers = bin_centers[nonzero_mask]
plot_counts = bin_counts[nonzero_mask]

# ============================================================
# 10. Plot
# ============================================================
plt.figure(figsize=(11, 6.5))
ax = plt.gca()

# ============================================================
# 11. Four-sided frame
# ============================================================
# 左、右、下边框，及 ★ 重新加回来的上边框
for spine in ['left', 'right', 'bottom', 'top']:
    ax.spines[spine].set_visible(True)

# ============================================================
# 12. Spectrum bars
# ============================================================
ax.bar(
    plot_centers, plot_counts, 
    width=np.diff(bin_edges)[nonzero_mask], # 柱宽随 bins 自动变化
    align="center", color="darkred", 
    edgecolor="none", linewidth=0           # 不加柱子边框
)

# ============================================================
# 13. Y axis range
# ============================================================
max_count = np.max(bin_counts)
y_lim_max = max_count * 1.18 if max_count > 0 else 10
ax.set_ylim(0, y_lim_max)

# ============================================================
# 14. X axis range and ticks
# ============================================================
ax.set_xlim(0, 2 * np.pi * 1.01)
ax.set_xticks([np.pi, 2 * np.pi])
ax.set_xticklabels([r"$\pi$", r"$2\pi$"], fontsize=11)

# ============================================================
# 15. Y axis ticks
# ============================================================
ax.yaxis.set_major_locator(MaxNLocator(nbins=8, integer=True))

# ============================================================
# 16. Labels & Title
# ============================================================
ax.set_xlabel("Argument of eigenvalues", fontsize=15, labelpad=10)
ax.set_ylabel("Multiplicity of eigenvalues", fontsize=15)
ax.set_title(f"The spectrum for Rule {rule_number}, n={n}", fontsize=17, fontweight="bold", pad=15)

# ============================================================
# 17. Grid
# ============================================================
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

# ============================================================
# 18. Zero eigenvalue ratio
# ============================================================
# 使用 text + bbox，不使用 Patch / Legend (避免出现彩色小矩形)
ax.text(
    0.985, 0.955, f"Zero eigenvalue ratio: {zero_mode_ratio:.8f}",
    transform=ax.transAxes, ha="right", va="top", fontsize=14,
    # ★ 给文字加一个黑色矩形框
    bbox=dict(boxstyle="square,pad=0.25", facecolor="white", edgecolor="black", linewidth=1.0)
)

# ============================================================
# 19. Save PDF
# ============================================================
filename = os.path.join(save_dir, f"Rule{rule_number}_n{n}.pdf")
plt.savefig(filename, format="pdf", bbox_inches="tight")

print("=" * 75)
print("Figure saved as:\n", filename)
print("=" * 75)

plt.show()

# ============================================================
# 20. Final statistics
# ============================================================
print("\n" + "=" * 75)
print("FINAL RESULTS")
print("=" * 75)
print(f"Rule                : {rule_number}")
print(f"n                   : {n}")
print(f"Total states        : {N:,}")
print(f"Cycle states        : {unit_circle_count:,}")
print(f"Transient states    : {N - unit_circle_count:,}")
print(f"Non-zero Mode Ratio : {nonzero_mode_ratio:.8f}")
print(f"Zero Mode Ratio     : {zero_mode_ratio:.8f}")
print(f"Number of cycles    : {len(cycle_lengths):,}")
print(f"Maximum cycle length: {cycle_lengths.max():,}")
print(f"Total runtime       : {time.time() - start_total:.2f} s")
print("=" * 75)