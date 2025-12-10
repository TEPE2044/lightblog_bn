# 命令行工具使用说明

## 启动项目
```bash
uvicorn src.main:app --reload --port 12404
```

## 更新requirements.txt
```bash
pip freeze > requirements.txt
```

## 同步数据库
```bash
alembic upgrade head
```

## 生成数据库迁移文件
### WARNING!!! 此命令只有在模型有变更时才需要执行
```bash
# alembic revision --autogenerate -m "init user table"
```