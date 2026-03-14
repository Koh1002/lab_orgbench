"""
使用方法:
  python -m orgbench pilot          # パイロット実行
  python -m orgbench main           # 本実験実行
  python -m orgbench judge          # 評価のみ実行
  python -m orgbench analyze        # 分析のみ実行
"""
import asyncio
import sys

from .runner import run_experiment
from .analysis import manipulation_check, estimate_effect_sizes


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m orgbench [pilot|main|judge|analyze]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "pilot":
        asyncio.run(run_experiment(
            experiment_yaml="configs/experiment.yaml",
            phase="pilot",
        ))
    elif cmd == "main":
        asyncio.run(run_experiment(
            experiment_yaml="configs/experiment_main.yaml",
            phase="main",
        ))
    elif cmd == "analyze":
        print("=== 操作チェック ===")
        mc = manipulation_check()
        print(f"  {mc}")
        print("\n=== 効果量推定 ===")
        es = estimate_effect_sizes()
        for dim, vals in es.items():
            if isinstance(vals, dict):
                print(f"  {dim}: η²={vals['eta_squared']:.4f}, "
                      f"d(single vs best)={vals['cohens_d_single_vs_best']:.4f}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
