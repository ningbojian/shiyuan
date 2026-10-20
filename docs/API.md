# 氏源 JSON API v1

只读接口，用于复用姓氏目录、人物与元数据。所有数据为课程演示整理，分布强度是 0–100 的示意值，不是人口统计。

- 基础路径：`/api/v1/`
- 仅支持 `GET`；其他方法返回 `405`。
- 不需要 CSRF token，也不提供写操作。
- 响应统一为：

```json
{"code": 0, "message": "ok", "data": {}}
```

失败时 `code` 非 0，`data` 为 `null`，HTTP 状态码表示错误类型：

```json
{"code": 404, "message": "未找到该姓氏。", "data": null}
```

## 分页

列表接口支持 `page`（默认 1）与 `page_size`（默认 20，上限 100）。`data` 中包含：

| 字段 | 说明 |
|---|---|
| `results` | 当前页结果 |
| `page` | 当前页码 |
| `page_size` | 实际生效的每页条数 |
| `pages` | 总页数 |
| `total` | 总条数 |

## GET /api/v1/surnames/

列出姓氏。查询参数：

| 参数 | 说明 |
|---|---|
| `q` | 匹配姓氏、拼音、首字母、别名、摘要 |
| `initial` | 拼音首字母 A–Z（不区分大小写） |
| `province` | 省份 slug，如 `hebei` |
| `page` / `page_size` | 分页 |

```bash
curl "http://127.0.0.1:8000/api/v1/surnames/?q=li&page_size=5"
```

结果字段：`second_name`、`slug`、`pinyin`、`initial`、`summary`。

## GET /api/v1/surnames/&lt;slug&gt;/

单个姓氏详情，除列表字段外还包含：

| 字段 | 说明 |
|---|---|
| `aliases` | 别名数组 |
| `base_information` / `origin` / `migration_text` / `distribution_text` / `culture` | 纯文本资料 |
| `keywords` | `[{"name": str, "value": int}]`，权重 1–100 |
| `source_note` / `is_demo` | 来源说明与演示标记 |
| `distributions` | `province`、`map_name`、`intensity`（0–100 示意值） |
| `figures` | `name`、`slug`、`dynasty`、`birth_year`、`death_year` |
| `migration_events` | `dynasty`、`from_province`、`to_province`、`description`、`order` |
| `relations` | `relation_type`、`relation_label`、`target_surname`、`target_clan`、`description` |

```bash
curl "http://127.0.0.1:8000/api/v1/surnames/li/"
```

## GET /api/v1/search/

搜索姓氏，参数与 `/surnames/` 相同。`q` 为空时返回空结果（`total` 为 0），不返回全量目录。

```bash
curl "http://127.0.0.1:8000/api/v1/search/?q=%E6%9D%8E"
```

## GET /api/v1/figures/

历史人物列表。查询参数：

| 参数 | 说明 |
|---|---|
| `dynasty` | 朝代 slug，如 `tang` |
| `surname` | 姓氏 slug，如 `li` |
| `page` / `page_size` | 分页 |

结果字段：`name`、`slug`、`dynasty`、`surname`、`surname_slug`、`birth_year`、`death_year`、`info`。

```bash
curl "http://127.0.0.1:8000/api/v1/figures/?dynasty=tang"
```

## GET /api/v1/meta/

返回筛选用元数据：

- `provinces`：`name`、`slug`
- `dynasties`：`name`、`slug`、`order`
- `initials`：目录中出现过的首字母数组，已排序

## 兼容与限制

- 字段只增不改；新增字段不会改变现有字段含义。
- 当前无认证、无限流；公开部署前应加缓存与网关限流。
- 演示数据不构成学术依据，引用请先阅读 `docs/DATA.md`。
