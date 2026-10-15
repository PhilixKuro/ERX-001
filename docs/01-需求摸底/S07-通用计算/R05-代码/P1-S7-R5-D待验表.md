# P1-S7-R5 D待验表

| 编号 | 对应任务 | 技术假设 | 验证方式 | 判定 | 证据 |
|---|---|---|---|---|---|
| HT-001 | TS-001 | Ruff 0.14.10 可装入 bench 环境，bench setup requirements --python 后仍可运行 | 实装、重装依赖、复查版本 | go | pip 实装成功；`bench setup requirements --python` 退出 0；重装后 `env/bin/ruff --version` 输出 `ruff 0.14.10`。完整输出在 `frappe-bench/logs/s7-r5-requirements.log` |

该事实验证在本轮容器中执行；不依赖此结果的工作先记录现有测试基线。

## 复核建议

验证覆盖当前容器内全部七个 app 的 Python 依赖重装；没有重建容器或运行 `docker/up.sh`。初次直连 PyPI 超时，重试采用 `docker/.env` 已有代理。复验命令：容器内 `bench setup requirements --python` 后运行 `env/bin/ruff --version`。
