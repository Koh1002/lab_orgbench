# H4・H6 検証結果

> 実行日: 2026-03-15
> データ: 実験A (60 runs) + 全Phase1データ (150 runs with step traces)

---

## H4: Mesh vs Hub — Topology-Dependent Information Preservation

### CFO/CDO の飽和確認

| Config | CFO avg_in | CFO CR | CDO avg_in | CDO CR |
|--------|-----------|--------|-----------|--------|
| flat_hub | 1,665 | **0.332** | 1,897 | **0.255** |
| flat_mesh | **7,684** | **0.057** | **7,988** | **0.059** |
| anchor | 1,643 | 0.351 | 1,904 | 0.228 |

**flat_mesh で CFO/CDO の入力が4.6倍に増加し、CR が 0.33→0.06 に崩壊**。
チャネル飽和が明確に確認された。

### しかし品質はflat_meshが最高（OQ=3.17-3.23）

CFO/CDO はレビュアー（主経路外）なので飽和しても品質に影響しない。
むしろ mesh により CEO への入力が増加（5,660 vs flat_hub 2,910）し、品質が向上。

**H4の結論**: 支持。mesh は弱いエージェント（CFO/CDO）を飽和させるが、
それが主経路外であれば品質に無害。主経路エージェントの容量が十分であればmesh優位。

---

## H6: CEO Augmentation — Input Volume as Quality Driver

### CEO input tokens vs OQ

**Pearson r = 0.317, p < 0.0001 (n=150)**

| Config | CEO input | OQ |
|--------|----------|-----|
| flat_mesh | 10,719 | 3.23 |
| deep_passthrough | 6,814 | 3.10 |
| flat_hub | 5,220 | 3.07 |
| anchor | 7,079 | 3.03 |
| chain_2 | 1,379 | 2.83 |
| chain_4 | 3,072 | 2.10 |

**H6の結論**: 支持。CEOへの入力量と品質にr=0.317の有意な正相関。
CEOは情報増幅チャネルとして機能し、より多くの入力からより良い出力を生成する。
