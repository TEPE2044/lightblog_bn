# 命令行工具使用说明

## 启动项目
```bash
uvicorn src.main:app --reload --port 12404 --log-level debug
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
### WARNING!!! 不要再使用`Base.metadata.create_all(bind=engine)`，请使用Alembic进行数据库迁移
```bash
# $env:PYTHONUTF8="1"
# alembic revision --autogenerate -m "init user table"
```