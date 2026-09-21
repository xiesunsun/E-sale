# Milestone 0 — Understand One Request

## 这一关只回答什么

执行下面的命令后：

```bash
curl -i \
  -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"product_id": 1001, "quantity": 2}'
```

一条记录如何从终端出发，经过网络和 Python 程序，最终出现在 `esale.db` 中？

最小运行模型：

```text
curl 进程
    │  HTTP bytes
    ▼
操作系统 socket
    │
    ▼
Uvicorn 所在的 Python 进程
    │  ASGI call
    ▼
FastAPI 路由与 Pydantic 校验
    │  Python function call
    ▼
create_order()
    │  SQL string + parameters
    ▼
Python sqlite3 module / SQLite library
    │  file I/O
    ▼
esale.db
```

这张图只是待验证的初始模型，不是需要背诵的最终答案。

## 本关边界

允许研究：

- shell 如何启动 `curl` 和 `uvicorn`；
- 进程与 Python library 的区别；
- socket 与 HTTP 的最小关系；
- Uvicorn、ASGI、FastAPI 分别扮演什么角色；
- Pydantic 如何把 JSON 变成 Python 对象；
- 参数化 SQL 由谁执行；
- SQLite 为何不是另一个服务进程；
- `commit()` 与数据库文件可见变化的最小理解。

暂不研究：

- 支付和退款业务；
- 并发请求、锁、隔离级别和 WAL 细节；
- PostgreSQL、Redis、消息队列和微服务；
- 完整的操作系统网络栈或 SQLite 源码；
- Agent 和 Agent Eval。

遇到这些问题时，把它们写入 `questions-parking-lot.md`。

## 实验 1：建立基线

先不要运行，写下预测：

1. 会出现几个进程？它们分别是谁？
2. 哪一部分在监听 `8000` 端口？
3. JSON 在哪一步变成 `OrderCreate`？
4. SQL 是 FastAPI、Python 还是 SQLite 执行的？
5. 如果不调用 `commit()`，关闭连接后是否还能看到新订单？

然后运行：

```bash
uv sync
uv run uvicorn app.main:app
```

在另一个终端执行一次 POST、一次 GET 和一次数据库查询：

```bash
curl -i -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"product_id": 1001, "quantity": 2}'

curl -i http://127.0.0.1:8000/orders/1

sqlite3 esale.db 'SELECT id, product_id, quantity, status FROM orders;'
```

记录实际现象，特别是 HTTP 状态码、响应 JSON 和数据库中的行。

## 实验 2：用错误定位边界

每次只制造一种错误，并在运行前预测错误由哪一层返回。

### 无效 JSON 字段

```bash
curl -i -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"product_id": 1001, "quantity": 0}'
```

观察：请求有没有进入 `create_order()`？为什么？

### 不存在的订单

```bash
curl -i http://127.0.0.1:8000/orders/999999
```

观察：为什么这是 404，而上一个错误不是 404？是谁做出的决定？

### 服务没有运行

停止 Uvicorn，再执行 GET。

观察：这次为什么没有 JSON 错误响应？错误发生在 HTTP 应用之前还是之后？

## 实验记录模板

每次学习复制下面这段，不追求长篇笔记：

```text
日期：
命令 / 输入：
运行前预测：
实际现象：
预测与现实的差异：
本次只新增的概念（最多 2 个）：
我现在能解释的完整链路：
仍然解释不了的问题：
```

## 闭卷验收

关闭代码和资料，完成以下任务：

- 画出 `curl → esale.db` 的完整路径；
- 明确指出图中的进程、library、文件和网络边界；
- 解释 Uvicorn、ASGI、FastAPI、Pydantic、`sqlite3` 各自的职责；
- 解释 SQL 由谁解析和执行；
- 解释为什么 Python 进程退出后数据仍然存在；
- 解释为什么 `GET /orders/999999` 和“服务未启动”是不同层的失败；
- 不参考现有实现，写出一个最小的 `POST /orders` 处理流程伪代码。

全部能够讲清楚，并且能用实验现象支撑解释后，才进入 v0.2。接口“能用”本身不算过关。

## 请 AI 做验收时使用

```text
你现在是 E-sale Systems 课程的验收员，不是讲师。
当前关卡是 Milestone 0：解释一次 POST /orders 如何从 curl 到 SQLite 文件。
请一次只问我一个问题，优先追问我解释中的断点。
不要提前讲事务、并发、WAL、PostgreSQL 或微服务。
不要直接给完整答案；先让我预测和解释。
最后给我一个最小故障场景，让我判断失败发生在哪一层。
```
