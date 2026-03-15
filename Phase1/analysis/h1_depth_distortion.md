# H1 検証結果: Information Distortion Curve

> 実行日: 2026-03-15
> データ: 実験B (chain_2~6, 75 runs) + 実験C (tracer, 36 runs)

---

## 1. Chain Depth vs Quality（実験B）

| chain | depth | review | OQ | n |
|-------|-------|--------|-----|---|
| chain_2 | 2 | no | 2.83 | 30 |
| chain_3 | 3 | no | 2.50 | 30 |
| chain_4 | 4 | no | 2.04 | 48 |
| chain_5 | 5 | yes | 2.20 | 30 |
| chain_6 | 6 | yes | 2.30 | 30 |

### chain_2~4（レビューなし、純粋なdepth効果）
- **Pearson r = -0.996**（ほぼ完全な線形相関）
- **勾配 = -0.396 OQ/depth**（1段追加あたり -0.40 の品質低下）
- Depth-Distortion Principle を強く支持

### chain_5~6（レビューあり）
- レビューゲートが品質を部分的に回復（chain_4=2.04 → chain_5=2.20, chain_6=2.30）
- しかし chain_2 (2.83) には遠く及ばない
- レビューは D_k^noise を軽減するが、蓄積された D_k^filter は回復不能

## 2. Tracer Survival Rate（実験C）

### 構成別最終TSR
| Config | TSR | n |
|--------|-----|---|
| flat_mesh | **0.50** | 9 |
| chain_4 | 0.20 | 9 |
| flat_hub | 0.18 | 9 |
| anchor | 0.16 | 9 |

### ステップ別TSR（anchor/t01_tracer/rep1）
| Step | Agent | TSR | 検出数/10 |
|------|-------|-----|----------|
| 0 | CEO | 0.70 | 7 |
| 1 | **TL** | **0.20** | **2** |
| 2 | Researcher | 0.10 | 1 |
| 3 | Writer | 0.10 | 1 |
| 4 | CFO | 0.00 | 0 |
| 5 | CDO | 0.10 | 1 |
| 6 | CEO(統合) | 0.10 | 1 |

### 主要な発見

1. **TLステップで70%→20%に急落**: 10個中5個のトレーサーがTL1段で消失。D_k^filter の直接測定値 = 0.50（トレーサーベース）

2. **flat_mesh のTSR=0.50 が最高**: mesh通信により、CEO統合ステップにより多くの情報が届く。anchor(0.16)の3倍。

3. **Researcher以降はほぼ横ばい (0.10)**: TLでの大幅な情報損失の後、残った情報は比較的保持される。ボトルネックはTL。

## 3. 論文への反映

- Information Distortion Curve: chain_2~4 の r=-0.996 は Figure の中核
- TSR step-by-step: TLでの急落を Figure で可視化
- mesh の情報保存優位性: flat_mesh TSR=0.50 vs anchor TSR=0.16
