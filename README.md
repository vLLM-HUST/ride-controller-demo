# RIDE Controller Demo

独立 Controller 开发模板。RIDE 是控制平面，Ray 是执行底座；本仓库只实现一个
可观察的 Controller 进程，不执行请求调度、不转发模型请求、不宣称性能收益。

## 安装与部署

需要支持 `ride.controllers` entry point 的 RIDE 版本。
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
