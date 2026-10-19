# 路由与接口摘要

## 页面路由

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/user/` | 首页（`/user/index/`） |
| GET | `/user/log/` | 登录页 |
| GET | `/user/register/` | 注册页 |
| GET | `/user/personal/` | 个人中心（需登录） |
| GET | `/surname/search/` | 姓氏搜索/热门列表 |
| GET | `/surname/index/?surname=李` | 姓氏详情与图表 |
| GET | `/surname/information/` | 项目资料 |
| GET | `/surname/science/` | 姓氏科普 |
| GET | `/surname/announce/` | 公告 |
| GET | `/surname/developer/` | 团队与分工 |
| GET | `/surname/introduction/` | 网页介绍 |

## 用户接口

| 方法 | 路径 | 参数 | 返回 |
|---|---|---|---|
| GET | `/user/getToken/` | 无 | `{"token": "..."}` |
| POST | `/user/create/` | `name`, `account`, `code`, `surname?` | 成功重定向到个人中心；失败 JSON |
| POST | `/user/login/` | `account`, `code` | 成功重定向；失败渲染登录页 |
| POST | `/user/alter/` | `account`, `code?`, `name?`, `surname?` | JSON |
| POST | `/user/vip/` | `account`, `month` | JSON |
| GET/POST | `/user/comment/` | `action=find/add/delete/alter`, `account`, `content`, `newComment?` | JSON |
| GET | `/user/logout/` | 无 | 退出并重定向 |

## 评论接口示例

```bash
# 查询
curl "http://127.0.0.1:8000/user/comment/?action=find&account=demo"

# 新增
curl "http://127.0.0.1:8000/user/comment/?action=add&account=demo&content=hello"

# 删除
curl "http://127.0.0.1:8000/user/comment/?action=delete&account=demo&content=hello"
```

## 安全说明

这是课程原型，不是生产 API：

- 评论接口为了兼容原前端使用 GET 参数；生产环境应改为 POST + CSRF，并增加权限/审核；
- 原项目还存在明文密码、硬编码 `SECRET_KEY`、`DEBUG=True`、`ALLOWED_HOSTS=*` 和 CORS `*`；整理版已改为环境变量和 Django 密码 hash，并移除了 `Middle.MyCors`；
- 示例账号只存在本地 SQLite，请不要使用真实密码。

原始课程 `接口文档.pdf` 描述的姓氏 API 与当前整理版页面路由并不完全一致；本文件以仓库中实际实现的 `user`/`Surname` 路由为准。
