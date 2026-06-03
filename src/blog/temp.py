# 重构blog模块
# 破坏性变更：删除mlog类型，不存在音乐博客类型

# TODO:blog/draft CRUD
# 博客草稿通用方法，用id区分
'''
1. create_blog 创建博客/草稿
2. update_blog 更新博客/草稿
3. delete_blog 删除博客/草稿
4. get_blog_by_id 获取对应id的博客/草稿详情
5. get_my_blog 获取个人博客/草稿(游标分页)
6. get_blog_by_uid 获取对应uid的所有博客/草稿（游标分页）
'''

# TODO: 博客推荐
'''
1. get_recommend_blog 个性化推荐
2. get_top_blog 热门博客推荐（主页推荐）
'''

# TODO: 草稿发布
'''
1. publish_draft 发布草稿为博客
'''

# TODO: 热门标签
'''
1. 
'''