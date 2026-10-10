# RIDE Controller Demo

独立 Controller 开发模板。RIDE 是控制平面，Ray 是执行底座；本仓库只实现一个
可观察的 Controller 进程，不执行请求调度、不转发模型请求、不宣称性能收益。

## 安装与部署

使用 RIDE main（适配器支持从提交 8023739 起提供），在 RIDE 仓库安装 `.[ray]`。
在管理进程和 Ray 执行节点安装本包，再启动或重启 RIDE 管理进程以发现适配器。

```sh
python -m pip install .
ride start --ray-address http://RAY_HEAD:8265
# 另一个工作区终端
ride start controller demo --name demo-main \
  --endpoint http://CONTROLLER_HOST:9012 --port 9012 --num-cpus 0.1 --num-gpus 0
ride describe controller demo-main
ride logs controller demo-main
ride stop controller demo-main
ride start controller demo-main
```

多节点时 endpoint 必须与实际执行节点匹配，用 `--resources` 明确节点资源约束。
当前 RIDE 不自动分配服务地址和端口。依赖可通过 Ray runtime_env 提供。

## 开发位置

- `__main__.py`：你的 Controller 服务与策略；独立进程，日志输出到标准输出。
- `adapter.py`：配置校验、进程命令、类型专用健康与身份探测。
- `pyproject.toml`：通过 `ride.controllers` 注册类型 `demo`。

将包名、注册类型、实际身份一起修改；不要复制 Request Throttling 的专用状态接口。
适配器提供 `command(spec) -> str` 和 `probe(spec) -> dict`，探测结果中的
`controller_ready` 必须是布尔值。异常由 RIDE 显示为探测失败。
进程生命周期与 Job ID 管理由 RIDE 承担，不要在 Controller 中操作集群。

## 验收范围

要求：Ray Job RUNNING、类型身份匹配、Ready、日志可见、重复启动不重复提交、
停止只影响本实例、恢复产生新的 Ready Job。
该模板不依赖 GPU 或模型；CPU 验收不能证明任何调度策略或硬件性能。
云端验收状态见 RIDE 仓库对应结果；未运行项不得写成 PASS。

## 可重复执行的验收

在已经运行 RIDE 的隔离云端环境中：

```sh
python scripts/acceptance.py --endpoint http://CONTROLLER_HOST:9012 \
  --address http://127.0.0.1:19100 --output demo-acceptance.json
```

此脚本会创建 demo-main、停止并恢复它，不能在同名生产实例上运行。
脚本不启动或停止 Ray 集群；运行完成后 demo-main 保持运行供检查。
验收证据必须先保存，再用 `ride stop controller demo-main` 清理。

2026-10-10，9450 临时 CPU Pod 的端到端验收 PASS：真实 Ray/RIDE/独立 Demo，
Ready、实际身份、重复启动、日志、停止和恢复均通过。RIDE 回归测试 14 项通过。
Pod 已删除，未申请 GPU/NPU。原始日志见 `results/cloud.log`，机器可读结果见
`results/acceptance.json`。这不证明模型请求处理或调度性能。
