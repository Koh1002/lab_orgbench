"""論文用の図を生成するスクリプト"""
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
from pathlib import Path

# IEEE形式に合わせたスタイル設定
plt.rcParams.update({
    'font.size': 9,
    'font.family': 'serif',
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
})

SCORES_PATH = Path("../results/judge/scores.csv")
FIGURES_DIR = Path("figures")

# 構成の表示順（overall_quality降順）
CONFIG_ORDER = [
    'flat_mesh', 'flat_hub', 'homo_haiku', 'matrix_hub', 'anchor',
    'deep_mesh', 'deep_tech', 'deep_finance', 'deep_noreview', 'homo_gpt', 'single_agent',
]

# 構成の短縮名
CONFIG_LABELS = {
    'flat_mesh': 'Flat-Mesh',
    'flat_hub': 'Flat-Hub',
    'homo_haiku': 'Homo-Haiku',
    'matrix_hub': 'Matrix-Hub',
    'anchor': 'Anchor',
    'deep_mesh': 'Deep-Mesh',
    'deep_tech': 'Deep-Tech',
    'deep_finance': 'Deep-Fin',
    'deep_noreview': 'Deep-NoRev',
    'homo_gpt': 'Homo-GPT',
    'single_agent': 'Single',
}

# カテゴリ別の色
CONFIG_COLORS = {
    'flat_mesh': '#2196F3',    # flat系: 青
    'flat_hub': '#64B5F6',
    'homo_haiku': '#FF9800',   # homo系: オレンジ
    'homo_gpt': '#FFB74D',
    'matrix_hub': '#4CAF50',   # matrix: 緑
    'anchor': '#9E9E9E',       # baseline: グレー
    'deep_mesh': '#E91E63',    # deep系: 赤/ピンク
    'deep_tech': '#F48FB1',
    'deep_finance': '#CE93D8',
    'deep_noreview': '#EF5350',
    'single_agent': '#795548',  # single: 茶
}

DIMS = ['feasibility', 'novelty', 'market_insight', 'financial_rigor', 'technical_depth', 'overall_quality']
DIM_LABELS = ['Feasibility', 'Novelty', 'Market\nInsight', 'Financial\nRigor', 'Technical\nDepth', 'Overall\nQuality']


def load_scores():
    """スコアCSVを読み込み"""
    scores = defaultdict(lambda: defaultdict(list))
    with open(SCORES_PATH, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            cfg = row['config_name']
            for d in DIMS:
                scores[cfg][d].append(float(row[d]))
    return scores


def fig1_overall_quality_bar(scores):
    """Fig 1: 構成別overall_quality棒グラフ（エラーバー付き）"""
    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    configs = CONFIG_ORDER
    means = [np.mean(scores[c]['overall_quality']) for c in configs]
    stds = [np.std(scores[c]['overall_quality']) for c in configs]
    colors = [CONFIG_COLORS[c] for c in configs]
    labels = [CONFIG_LABELS[c] for c in configs]

    bars = ax.bar(range(len(configs)), means, yerr=stds, capsize=2,
                  color=colors, edgecolor='black', linewidth=0.5, width=0.7,
                  error_kw={'linewidth': 0.8})

    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Overall Quality (1-5)')
    ax.set_ylim(0, 5)
    ax.axhline(y=np.mean(scores['anchor']['overall_quality']), color='gray',
               linestyle='--', linewidth=0.7, alpha=0.7, label='Anchor baseline')
    ax.legend(loc='upper right', fontsize=7)
    ax.grid(axis='y', alpha=0.3, linewidth=0.5)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig1_overall_quality.pdf')
    fig.savefig(FIGURES_DIR / 'fig1_overall_quality.png')
    print("  fig1_overall_quality saved")
    plt.close(fig)


def fig2_radar_chart(scores):
    """Fig 2: 代表4構成のレーダーチャート"""
    selected = ['flat_mesh', 'anchor', 'homo_haiku', 'single_agent']
    colors_sel = ['#2196F3', '#9E9E9E', '#FF9800', '#795548']
    labels_sel = ['Flat-Mesh', 'Anchor', 'Homo-Haiku', 'Single']

    angles = np.linspace(0, 2 * np.pi, len(DIMS), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(3.5, 3.2), subplot_kw=dict(polar=True))

    for cfg, color, label in zip(selected, colors_sel, labels_sel):
        values = [np.mean(scores[cfg][d]) for d in DIMS]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=1.2, markersize=3, label=label, color=color)
        ax.fill(angles, values, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(DIM_LABELS, fontsize=7)
    ax.set_ylim(0, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=7)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=7)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig2_radar.pdf')
    fig.savefig(FIGURES_DIR / 'fig2_radar.png')
    print("  fig2_radar saved")
    plt.close(fig)


def fig3_effect_sizes(scores):
    """Fig 3: 次元別η²とCohen's dの棒グラフ"""
    # 効果量を計算
    effect_data = {}
    for dim in DIMS:
        groups = [scores[c][dim] for c in CONFIG_ORDER]
        all_vals = [x for g in groups for x in g]
        grand_mean = np.mean(all_vals)
        ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups)
        ss_total = sum((x - grand_mean)**2 for x in all_vals)
        eta_sq = ss_between / ss_total if ss_total > 0 else 0

        # Cohen's d: single vs best multi
        single = scores['single_agent'][dim]
        best_multi_name = max(
            [c for c in CONFIG_ORDER if c != 'single_agent'],
            key=lambda c: np.mean(scores[c][dim])
        )
        best_multi = scores[best_multi_name][dim]
        n1, n2 = len(single), len(best_multi)
        pooled_sd = math.sqrt(((n1-1)*np.var(single, ddof=1) + (n2-1)*np.var(best_multi, ddof=1)) / (n1+n2-2))
        d = (np.mean(best_multi) - np.mean(single)) / pooled_sd if pooled_sd > 0 else 0

        effect_data[dim] = {'eta_sq': eta_sq, 'cohens_d': d}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.5))

    x = range(len(DIMS))
    dim_short = ['Feas.', 'Nov.', 'Mkt.', 'Fin.', 'Tech.', 'OQ']

    # η²
    eta_vals = [effect_data[d]['eta_sq'] for d in DIMS]
    bars1 = ax1.bar(x, eta_vals, color='#5C6BC0', edgecolor='black', linewidth=0.5, width=0.6)
    ax1.axhline(y=0.14, color='red', linestyle='--', linewidth=0.7, label='Large threshold')
    ax1.axhline(y=0.06, color='orange', linestyle='--', linewidth=0.7, label='Medium threshold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(dim_short)
    ax1.set_ylabel('$\\eta^2$')
    ax1.set_title('(a) $\\eta^2$ (between configurations)')
    ax1.legend(fontsize=6, loc='upper right')
    ax1.set_ylim(0, 0.55)
    ax1.grid(axis='y', alpha=0.3)

    # Cohen's d
    d_vals = [effect_data[d]['cohens_d'] for d in DIMS]
    bars2 = ax2.bar(x, d_vals, color='#EF5350', edgecolor='black', linewidth=0.5, width=0.6)
    ax2.axhline(y=0.8, color='red', linestyle='--', linewidth=0.7, label='Large threshold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(dim_short)
    ax2.set_ylabel("Cohen's $d$")
    ax2.set_title("(b) Cohen's $d$ (Single vs. Best Multi)")
    ax2.legend(fontsize=6, loc='upper right')
    ax2.set_ylim(0, 2.2)
    ax2.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig3_effect_sizes.pdf')
    fig.savefig(FIGURES_DIR / 'fig3_effect_sizes.png')
    print("  fig3_effect_sizes saved")
    plt.close(fig)


def fig4_dimension_heatmap(scores):
    """Fig 4: 構成×次元のヒートマップ"""
    fig, ax = plt.subplots(figsize=(4.5, 3.5))

    matrix = []
    for cfg in CONFIG_ORDER:
        row = [np.mean(scores[cfg][d]) for d in DIMS]
        matrix.append(row)
    matrix = np.array(matrix)

    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=1, vmax=5)

    ax.set_xticks(range(len(DIMS)))
    ax.set_xticklabels(DIM_LABELS, fontsize=7)
    ax.set_yticks(range(len(CONFIG_ORDER)))
    ax.set_yticklabels([CONFIG_LABELS[c] for c in CONFIG_ORDER], fontsize=7)

    # 値を表示
    for i in range(len(CONFIG_ORDER)):
        for j in range(len(DIMS)):
            val = matrix[i, j]
            color = 'white' if val < 2.2 or val > 4.2 else 'black'
            ax.text(j, i, f'{val:.1f}', ha='center', va='center', fontsize=6.5, color=color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Score (1-5)', fontsize=8)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig4_heatmap.pdf')
    fig.savefig(FIGURES_DIR / 'fig4_heatmap.png')
    print("  fig4_heatmap saved")
    plt.close(fig)


def fig5_cost_quality(scores):
    """Fig 5: コスト vs 品質の散布図"""
    import json, glob

    cfg_cost = defaultdict(float)
    for f in sorted(glob.glob('../results/runs/*/run_meta.json')):
        d = json.load(open(f))
        cfg_cost[d['config_name']] += d['total_cost_usd']

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    for cfg in CONFIG_ORDER:
        cost = cfg_cost[cfg]
        oq = np.mean(scores[cfg]['overall_quality'])
        ax.scatter(cost, oq, c=CONFIG_COLORS[cfg], s=60, edgecolors='black',
                   linewidth=0.5, zorder=5)
        # ラベル位置の調整
        offset_x, offset_y = 0.05, 0.08
        if cfg == 'flat_hub':
            offset_y = -0.15
        elif cfg == 'homo_haiku':
            offset_x = -0.3
            offset_y = -0.15
        ax.annotate(CONFIG_LABELS[cfg], (cost, oq),
                    xytext=(cost + offset_x, oq + offset_y),
                    fontsize=6, ha='left')

    ax.set_xlabel('Total Cost (USD, 25 runs)')
    ax.set_ylabel('Overall Quality (1-5)')
    ax.set_ylim(1.0, 4.0)
    ax.grid(alpha=0.3, linewidth=0.5)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig5_cost_quality.pdf')
    fig.savefig(FIGURES_DIR / 'fig5_cost_quality.png')
    print("  fig5_cost_quality saved")
    plt.close(fig)


def fig6_pairwise_comparison(scores):
    """Fig 6: RQ別のペア比較（箱ひげ図）"""
    fig, axes = plt.subplots(2, 2, figsize=(7, 5))

    dim = 'overall_quality'

    # RQ2: flat vs deep
    ax = axes[0, 0]
    pairs = [('flat_hub', 'anchor'), ('flat_mesh', 'deep_mesh')]
    positions = []
    data = []
    labels = []
    colors = []
    pos = 0
    for flat, deep in pairs:
        data.append(scores[flat][dim])
        data.append(scores[deep][dim])
        positions.extend([pos, pos + 0.8])
        labels.extend([CONFIG_LABELS[flat], CONFIG_LABELS[deep]])
        colors.extend([CONFIG_COLORS[flat], CONFIG_COLORS[deep]])
        pos += 2
    bp = ax.boxplot(data, positions=positions, widths=0.6, patch_artist=True,
                    showfliers=False, medianprops=dict(color='black', linewidth=1.5))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=7, rotation=20, ha='right')
    ax.set_ylabel('Overall Quality')
    ax.set_title('(a) RQ2: Flat vs. Deep', fontsize=9)
    ax.set_ylim(0.5, 5.5)
    ax.grid(axis='y', alpha=0.3)

    # RQ3: hub vs mesh
    ax = axes[0, 1]
    pairs = [('flat_hub', 'flat_mesh'), ('anchor', 'deep_mesh')]
    positions = []
    data = []
    labels = []
    colors = []
    pos = 0
    for hub, mesh in pairs:
        data.append(scores[hub][dim])
        data.append(scores[mesh][dim])
        positions.extend([pos, pos + 0.8])
        labels.extend([CONFIG_LABELS[hub], CONFIG_LABELS[mesh]])
        colors.extend([CONFIG_COLORS[hub], CONFIG_COLORS[mesh]])
        pos += 2
    bp = ax.boxplot(data, positions=positions, widths=0.6, patch_artist=True,
                    showfliers=False, medianprops=dict(color='black', linewidth=1.5))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=7, rotation=20, ha='right')
    ax.set_ylabel('Overall Quality')
    ax.set_title('(b) RQ3: Hub vs. Mesh', fontsize=9)
    ax.set_ylim(0.5, 5.5)
    ax.grid(axis='y', alpha=0.3)

    # RQ4: review vs no review
    ax = axes[1, 0]
    data = [scores['anchor'][dim], scores['deep_noreview'][dim]]
    colors_r = [CONFIG_COLORS['anchor'], CONFIG_COLORS['deep_noreview']]
    bp = ax.boxplot(data, positions=[0, 1], widths=0.6, patch_artist=True,
                    showfliers=False, medianprops=dict(color='black', linewidth=1.5))
    for patch, color in zip(bp['boxes'], colors_r):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Anchor\n(w/ review)', 'Deep-NoRev\n(w/o review)'], fontsize=7)
    ax.set_ylabel('Overall Quality')
    ax.set_title('(c) RQ4: Review Protocol', fontsize=9)
    ax.set_ylim(0.5, 5.5)
    ax.grid(axis='y', alpha=0.3)

    # RQ5: model homogeneity
    ax = axes[1, 1]
    data = [scores['homo_haiku'][dim], scores['anchor'][dim], scores['homo_gpt'][dim]]
    colors_m = [CONFIG_COLORS['homo_haiku'], CONFIG_COLORS['anchor'], CONFIG_COLORS['homo_gpt']]
    bp = ax.boxplot(data, positions=[0, 1, 2], widths=0.6, patch_artist=True,
                    showfliers=False, medianprops=dict(color='black', linewidth=1.5))
    for patch, color in zip(bp['boxes'], colors_m):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(['Homo-Haiku\n(all high)', 'Anchor\n(hetero)', 'Homo-GPT\n(all low)'], fontsize=7)
    ax.set_ylabel('Overall Quality')
    ax.set_title('(d) RQ5: Model Homogeneity', fontsize=9)
    ax.set_ylim(0.5, 5.5)
    ax.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig6_pairwise.pdf')
    fig.savefig(FIGURES_DIR / 'fig6_pairwise.png')
    print("  fig6_pairwise saved")
    plt.close(fig)


def main():
    scores = load_scores()
    print("Generating figures...")
    fig1_overall_quality_bar(scores)
    fig2_radar_chart(scores)
    fig3_effect_sizes(scores)
    fig4_dimension_heatmap(scores)
    fig5_cost_quality(scores)
    fig6_pairwise_comparison(scores)
    print("Done! All figures saved to", FIGURES_DIR)


if __name__ == '__main__':
    main()
