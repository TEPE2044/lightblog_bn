# 博客模块

- 符号说明: '!'为状态 '*'为键属性 '^'为计划接口

## 博客数据结构
- id /int 博客id *PRIMARY
- type /BlogEnum 博客类型 !调整中 + blog / notice 
- state /BlogStateEnum 博客状态 publish / draft / delete / ban
- title /str 博客标题
- content /str 博客内容
- create_at /datetime 创建时间
- update_at /datetime 更新时间
- rid /int 所属用户id *FOREIGNKEY
- cover /list[str] 博客封面图列表
- tags /List[Tag] 博客标签列表 *FOREIGNKEY

## 博客v1新版接口设计 统一前缀 /api/v1/blog
### 公共接口 博客/草稿CRUD
- POST /new 创建博客/草稿
- POST /update 更新博客/草稿
- POST /delete 删除博客/草稿
- POST /posts 获取博客/草稿列表（分页）
- GET /{blog_id} 获取博客/草稿详情
- GET /user/{user_id} 获取用户的博客/草稿列表（分页）

### 推送接口
- GET /daily 每日博客推荐（按标签推荐）
- GET /hot 热门博客(分页)
- GET /tags/hot 热门标签(固定排榜)

### 其他接口
- POST /upload/img 图片上传接口
- POST /upload/video 视频上传接口
- ^POST /ai/generate 博客内容生成接口（AI助写）
- POST /posts/editable 检测博客是否可编辑(ban/delete状态不可编辑，防止用户刻意修改已删除/封禁的博客) 