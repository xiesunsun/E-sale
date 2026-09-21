# E-sale 系统演化路线图

E-sale 的目标不是“实现商城”，而是亲历一个小型业务系统为何逐步演化成现代后端。每个阶段必须由当前系统中的具体问题触发。

## 四层能力地图

| 层级 | 系统范围 | 主要能力 |
| --- | --- | --- |
| Layer 1 | Single-machine Software | OS、HTTP、API、SQL、进程、线程、事务、测试、调试 |
| Layer 2 | Production Backend | PostgreSQL、缓存、队列、异步、重试、幂等、日志、指标、容器 |
| Layer 3 | Distributed System | 多实例、服务通信、复制、一致性、故障、高可用 |
| Layer 4 | AI-native System | Agent、Tool、Sandbox、Harness、State Verification、Evaluation |

这不是四份独立的技术清单。上层必须由下层已经出现的问题生长出来。

## 里程碑主线

| 版本 | 当前系统暴露的问题 | 允许引入的核心概念 | 过关证据 |
| --- | --- | --- | --- |
| **v0.1（当前）** | 一次请求怎样真正修改磁盘状态？ | HTTP、进程、Python library、SQL、SQLite | 闭卷画出并解释 `curl → database file` |
| v0.2 | 数据为何能在进程退出后保留？ | 文件、持久化、SQLite page 的最小模型 | 重启服务后解释数据为何仍存在 |
| v0.3 | 多步业务修改中途失败会怎样？ | 原子性、事务、commit、rollback | 制造中途失败并证明状态没有写一半 |
| v0.4 | 两个退款同时发生会怎样？ | race condition、隔离、锁 | 稳定复现错误，再用最小修改修复 |
| v0.5 | 手工验证越来越不可信怎么办？ | unit、integration、E2E 的边界 | 自动验证一个核心业务不变量 |
| v1.0 | SQLite 何时不够用？ | client/server DB、PostgreSQL、连接 | 能解释迁移解决了什么、增加了什么 |
| v1.1 | 重复请求会不会重复扣款或退款？ | idempotency key、重试语义 | 同一请求重复执行仍只生效一次 |
| v1.2 | 一个请求包含慢操作怎么办？ | background job、queue、worker、ack | 请求先返回，任务最终完成且可恢复 |
| v1.3 | 热数据访问慢怎么办？ | cache、TTL、cache-aside、一致性 | 测量收益并解释过期或脏数据 |
| v2.0 | 一台应用服务器不够怎么办？ | 多实例、无状态、LB、共享状态 | 两个实例提供一致行为 |
| v2.1 | 支付为何值得拆成独立服务？ | 网络调用、timeout、failure、retry | 注入延迟/丢响应并解释最终状态 |
| v2.2 | 跨服务状态写一半怎么办？ | outbox、Saga、最终一致性 | 注入崩溃后能恢复或补偿 |
| v2.3 | 数据库或服务挂掉怎么办？ | replication、failover、health check | 故障演练和恢复证据 |
| v2.4 | 线上出了什么问题？ | structured logging、metrics、tracing | 从观测信号定位一次注入故障 |
| v3.0 | 自然语言如何安全操作系统？ | Agent tool、权限、sandbox | Agent 只能执行被允许的业务动作 |
| v3.1 | 如何证明 Agent 真的完成任务？ | state verification、oracle、rollout | 通过最终数据库状态而非话术判定成功 |

版本号表达学习顺序，不是交付承诺。只有当前里程碑的验收证据完成后，才将下一行设为“当前”。

## 始终贯穿的业务不变量

后续功能出现时，系统必须逐步保护这些规则：

- 退款总额不能超过实际支付额；
- 已取消订单不能再次支付；
- 已全额退款订单不能再次退款；
- 库存不能小于零；
- 同一个业务请求无论重试多少次，只能产生一次效果；
- 支付成功最终必须对应正确的订单状态。

这些不变量是学习 correctness、测试、事务和分布式一致性的共同主线。当前 v0.1 尚未实现它们。
