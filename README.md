# E-sale
E-sale是一个逐步演化的软件工程学习项目
目标不是快速堆叠商城功能，而是从一个最小后端开始，让数据库，并发，测试，可靠性和分布式设计都由真实问题逐步引入

## Current Mileston

**Milestone 1-PostgreSQL Backend**
当前的系统已经从SQLite 单机数据库迁移到PostgreSQL，并具备
- FastAPI + Uvicorn HTTP API
- PostgreSQL 18
- pyscopg 3
- PostgreSQL connection pool
- 订单创建与查询
- 支付状态与CAS更新
- Transanction 保证支付状态与支付记录原子提交
- 并发支付回归测试
- PostgreSQL integration tests
- Github Actions + PostgreSQL CI service

当前请求链路
```text
HTTP Client
    ↓
Uvicorn
    ↓
FastAPI
    ↓
Connection Pool
    ↓
PostgreSQL
```
Requirements
- python 3.12+
- uv
- PostgreSQL

安装依赖
```python
uv sync
```
Database Setup
创建开发数据库
```
createdb esale
```
创建测试数据库
```
create esale_test
```
默认开发🔗
```
host=127.0.0.1 port=5432 dbname=esale
```
测试环境
```
export ESALE_TEST_DATABASE_URL="host=127.0.0.1 port=5432 dbname=esale_tes"
```
Run
```
uv run uvicorn app.main:app --port 8000
```
