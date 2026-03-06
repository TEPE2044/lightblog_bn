 # 命令行工具使用说明

## 在CMD进入虚拟环境
```bash
cd lightblog_bn
.venv\Scripts\activate    
```

## 启动项目
```bash
uvicorn src.main:app --reload --port 12404 --log-level debug
```

## 更新requirements.txt
```bash
pip freeze > requirements.txt
```

## 安装requirements.txt
```bash
pip install -r requirements.txt
```

## 同步数据库
```bash
$env:PYTHONUTF8="1"
alembic upgrade head
```

## WARNING!!! 回滚的是版本，revision成功只是生成了迁移文件，并没有执行迁移 
```bash
#alembic downgrade -1
```

## 生成数据库迁移文件
### WARNING!!! 此命令只有在模型有变更时才需要执行
### WARNING!!! 不要再使用`Base.metadata.create_all(bind=engine)`，请使用Alembic进行数据库迁移
```bash

# alembic revision --autogenerate -m "init user table"
```
## 解密keyhex
```python
bytes.fromhex('那个密码')
```

## StrawBerry接口与普通接口对比
| REST 概念            | GraphQL 草莓等价               |
| ------------------ | -------------------------- |
| Pydantic Model     | `@strawberry.type`         |
| `@router.get(...)` | `@strawberry.field`        |
| 依赖注入 `Depends`     | `info.context["xxx"]`（手动塞） |
| 路径参数 `/users/{id}` | 字段参数 `user(id: ID!)`       |
| 404/401 状态码        | 抛 `Exception` → `errors[]` |

## 修改分支的名称
### back_populates
- 目的是查询的时候可以双向查询，比如User查询它的Blogs，Blog查询它的User
- 要写就两边都写，不然就全都删掉
- 

## 配置WebHooks
- 需要多次尝试
- 必要的时候去除SSL验证
- 测试提交