# E-sale

E-sale 不是一个追求尽快堆满技术栈的商城 Demo，而是一个长期的软件工程学习项目：从最小的单机程序开始，只在当前系统暴露出真实问题时，才引入下一种抽象。

## 当前阶段

**v0.1 / Milestone 0 — Understand One Request**

当前唯一主问题：

> 执行一次 `POST /orders` 后，一条订单记录是怎样从终端经过 HTTP、操作系统、Python 进程、FastAPI、SQLite，最终进入数据库文件的？

这一阶段只包含：

- 一个 Python 进程；
- FastAPI + Uvicorn；
- SQLite；
- 创建订单和读取订单两个接口。

这一阶段故意不包含支付、退款、并发控制、Redis、消息队列、Docker、微服务和 Agent。它们已经记录在[学习路线图](study/00-roadmap.md)中，但还不是现在的问题。

## 运行

要求：Python 3.12 和 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync
uv run uvicorn app.main:app
```

服务启动时会在当前目录创建 `esale.db`。这个文件是本地实验数据，不提交到 Git。整理前已有的支付与并发实验数据库已原样保存在本机 `study/archive/pre-v0.1-esale.db`，不会参与当前里程碑。

在另一个终端执行：

```bash
curl -i \
  -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"product_id": 1001, "quantity": 2}'
```

然后读取刚才返回的订单（把 `1` 换成实际的订单 ID）：

```bash
curl -i http://127.0.0.1:8000/orders/1
```

也可以直接观察数据库：

```bash
sqlite3 esale.db 'SELECT * FROM orders;'
```

## 学习入口

- [学习约定与使用方法](study/README.md)
- [完整路线图](study/00-roadmap.md)
- [当前里程碑实验手册](study/01-milestone-0-understand-one-request.md)
- [暂不展开的问题](study/questions-parking-lot.md)

## 当前代码结构

```text
app/
├── __init__.py
├── db.py       # SQLite 连接和建表
└── main.py     # HTTP 边界和当前的两个接口
study/          # 固定课程、当前实验和延后问题
```

保持结构简单是当前阶段的一部分。只有当代码本身让某个职责难以理解或测试时，再拆分 `domain/`、`repository/`、`service/` 等目录。
