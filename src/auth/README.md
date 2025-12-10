# SQLALCHEMY 2.x
### scalar
- 注意scalars和scalar的区别
- 只要第一列的列表	`result.scalars().all()`	
- 只要第一列的第一个值	`result.scalars().first()`	
- 只要第一列的单个值（确定只有 1 行）	`result.scalar()` ← 直接拿标量	

