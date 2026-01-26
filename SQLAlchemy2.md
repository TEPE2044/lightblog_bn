# SQLAlchemy 查询结果获取方法速查表
假设有一个简单的用户表 `User`，里面有 id 和 name 两列。
（表结构：User(id, name) 里现有 3 行：1→alice，2→bob，3→cathy）

```python
from sqlalchemy import select
from sqlalchemy.orm import Session
session: Session = ...  # 已拿到的异步或同步会话
```

1. 只想拿“第一行”——用 `.first()`

```python
stmt = select(User).where(User.id >= 1).order_by(User.id)
row = session.execute(stmt).first()
print(row)            # (User(id=1, name='alice'),)
print(row[0].name)    # alice
```

- 返回：一个 `Row` 对象（本质是“元组”），没有数据就是 `None`  
- 内部自动 `LIMIT 1`，随便有几行都只拿第一条。

2. 想一次拿“全部行”——用 `.all()`

```python
rows = session.execute(stmt).all()
print(rows)
# [
#   (User(id=1, name='alice'),),
#   (User(id=2, name='bob'),),
#   (User(id=3, name='cathy'),)
# ]
```

- 返回：Python 列表，元素都是 `Row`  
- 空表就返回 `[]`

3. 只要“第一行第一列”——用 `.scalar()`

```python
name = session.execute(select(User.name).where(User.id == 1)).scalar()
print(name)           # alice
```

- 返回：真正的 Python 值（字符串/数字/…），没有数据就是 `None`  
- 如果 SQL 返回多行，也只拿第一行第一列，不会报错。

4. 必须“有且仅有一行一列”——用 `.scalar_one()`

```python
name = session.execute(select(User.name).where(User.id == 1)).scalar_one()
print(name)           # alice
```

- 0 行 → `NoResultFound` 异常  
- ≥2 行 → `MultipleResultsFound` 异常

5. 允许“没有”，但禁止“多”——用 `.scalar_one_or_none()`

```python
name = session.execute(select(User.name).where(User.id == 99)).scalar_one_or_none()
print(name)           # None
```

- 0 行 → 返回 `None`  
- 1 行 → 返回那唯一值  
- ≥2 行 → 抛 `MultipleResultsFound`

6. 整行“必须唯一”——用 `.one()`

```python
user_row = session.execute(select(User).where(User.id == 1)).one()
print(user_row)       # (User(id=1, name='alice'),)
```

- 0 行 → `NoResultFound`  
- 1 行 → 返回唯一 `Row`  
- ≥2 行 → `MultipleResultsFound`

7. 整行“0 或 1”——用 `.one_or_none()`

```python
user_row = session.execute(select(User).where(User.id == 99)).one_or_none()
print(user_row)       # None
```

# 下面把「写 SQL」时最容易混的四兄弟——

`.values()`、`.returning()`、`.on_conflict_do_nothing()`、`.update()`——

用“一条语句到底长什么样”给你对号入座，看完就不会再脸盲。

---

1. `.values()` —— 只是“放数据”的抽屉

出现位置：INSERT / UPDATE 语句

作用：告诉数据库“我要写入的列和值”

同步异步都一样，只是个构造器，本身不会发 SQL。

```python
from sqlalchemy import insert
stmt = insert(User).values(name='alice', age=18)
print(stmt)   # INSERT INTO user (name, age) VALUES (:name, :age)
```

---

2. `.returning()` —— 写完顺手把新数据拿回来

出现位置：INSERT / UPDATE / DELETE 后面

作用：在同一条 SQL里返回刚写进去（或改完）的行，省去再 SELECT 一次

返回值：仍在“语句对象”里，执行后才拿到真正的行/列

```python
from sqlalchemy import insert
stmt = (insert(User)
        .values(name='alice')
        .returning(User))          # 整行都要
row = (await session.execute(stmt)).one()   # 执行完立刻拿到 Row
print(row[0])   # User(id=4, name='alice')
```

只想拿主键也行：

```python
stmt = insert(User).values(name='bob').returning(User.id)
new_id = (await session.execute(stmt)).scalar_one()
```

---

3. `.on_conflict_do_nothing()` —— PostgreSQL 的“有就拉倒，无则插入”

出现位置：PostgreSQL 方言的 `insert` 后面

作用：碰到唯一约束冲突时什么都不干（也不会抛错）

返回值：仍是语句对象，执行后若无插入则返回空结果集

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert
stmt = (pg_insert(User)
        .values(name='alice')          # name 有唯一索引
        .on_conflict_do_nothing(index_elements=['name'])
        .returning(User.id))
row = (await session.execute(stmt)).first()
print(row)   # 如果 alice 已存在 → None；新插 → (4,)
```

---

4. `.update()` —— 专门负责“改”

出现位置：UPDATE 语句

作用：生成 UPDATE 语句，同样用 `.values()` 放“改后的值”

也能加 `.returning()` 把改完的数据拿回来

```python
from sqlalchemy import update
stmt = (update(User)
        .where(User.name == 'alice')
        .values(age=20)
        .returning(User))
row = (await session.execute(stmt)).one()
print(row[0])   # User(id=1, name='alice', age=20)
```

---

一句话总结  
- `.values()` 是“放数据”  
- `.returning()` 是“写完顺手拿回来”  
- `.on_conflict_do_nothing()` 是“PG 专属免冲突”  
- `.update()` 是“改数据”  

记住它们分别属于哪条 SQL 分支，就不会再张冠李戴。