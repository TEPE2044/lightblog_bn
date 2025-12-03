# 命令行工具使用说明

## 启动项目
```bash
uvicorn src.main:app --reload
```

## 更新requirements.txt
```bash
pip freeze > requirements.txt
```

## 同步新字段
```bash
alembic upgrade head  
```