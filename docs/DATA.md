# 数据说明（DATA）

氏源的数据以仓库内 `data/catalog.json` 为唯一可复现来源。数据库中的姓氏、分布、人物、迁徙与源流记录均可由该文件重建，不需要手工录入。

## 一句话结论

这是**课程展示用的整理数据**，不是权威人口统计。页面与接口中的“分布强度”只是可视化示意值，不能当作各省人口占比、排名或学术结论引用。

## 数据规模

| 内容 | 数量 |
|---|---|
| 姓氏 | 33（李、王、张、刘、陈、杨、赵、黄、周、吴、徐、孙、胡、朱、高、林、何、郭、马、罗、梁、宋、郑、谢、韩、唐、冯、于、董、萧、沈、叶、丁） |
| 历史人物 | 132（每姓 4 位） |
| 迁徙事件 | 66（每姓 2 条） |
| 源流关系 | 36（含马→赵、何→韩、叶→沈等跨姓关系） |
| 宗族节点 | 10（姬、嬴、子、妫、姜、祁、曹、妘、己、芈） |
| 省份 | 34（含港澳台） |
| 朝代 | 18（夏至中华民国） |

其中李、王、张、丁四姓的 `base_information`、`fam`、`mig`、`dis`、`ori`、`cul` 六个字段来自 `data/surnames/<姓>/` 下的课程原始文本，按原文完整迁入（`TextField`，不截断）。其余 29 姓与所有人物、事件、分布、关系文本为演示整理内容。

## 数据从哪来

1. **课程原始样本**：`data/surnames/` 保留李、王、张、丁的原始 `.txt`，是内容来源与回归样本；测试会逐字段比对 catalog 与原文是否一致（空文件除外）。
2. **演示扩展**：`scripts/generate_catalog.py` 依据姓氏、宗族、地域与人物元数据生成 29 个扩展姓氏的摘要、人物、迁徙、分布与关系文本。生成过程是确定性的，重复运行得到相同结果。
3. **参考项目**：`dutongjian.com` / `kxxhhh/Dutongjian` 与知乎项目页只用于借鉴产品结构（目录、人物/地点/事件网络、地图与时间轴、收藏/历史），**没有复制其文本、图片、数据或品牌**。

### 关于分布强度

`Distribution.intensity` 取值范围 0–100，表示“可视化上的相对强度”，不是百分比：

- 同一姓氏的多个省份强度之和可以大于 100；
- 数值由生成脚本按预设序列产生，不代表人口普查数据；
- 每条记录都有 `is_illustrative=True` 与 `source_note`，页面显示“演示数据 · 非权威统计”。

### 关于人物与迁徙

人物生卒年、朝代与事件描述来自常见历史常识的概述性整理，用于演示人物索引、朝代分组与时间轴；不保证完备，也不作为学术引用来源。所有演示记录均带 `source_note`，`is_demo=True`。

## 文件结构

```json
{
  "meta": {"version": 1, "generated_at": "2026-10-20", "disclaimer": "..."},
  "clans": [
    {"name": "姬姓", "slug": "ji-xing", "kind": "xing", "description": "..."}
  ],
  "surnames": [
    {
      "second_name": "李",
      "slug": "li",
      "pinyin": "li",
      "initial": "L",
      "aliases": ["李氏"],
      "summary": "60–120 字摘要",
      "base_information": "...",
      "ori": "...",
      "mig": "...",
      "dis": "...",
      "cul": "...",
      "fam": "兼容旧页面的名人长文本",
      "keywords": [{"name": "陇西", "value": 40}],
      "source_note": "来源与演示性质说明",
      "is_demo": true,
      "is_featured": true,
      "popularity": 100,
      "distributions": [
        {"province": "河北省", "intensity": 72, "is_illustrative": true, "source_note": "..."}
      ],
      "figures": [
        {"name": "李白", "slug": "li-bai", "dynasty": "唐朝", "info": "...",
         "birth_year": 701, "death_year": 762, "source_note": "...", "is_demo": true}
      ],
      "migration_events": [
        {"dynasty": "唐朝", "from_province": "河南省", "to_province": "福建省",
         "description": "...", "source_note": "...", "order": 1}
      ],
      "relations": [
        {"target_surname": "赵", "relation_type": "branch",
         "description": "...", "source_note": "..."}
      ]
    }
  ]
}
```

### 字段含义

| 字段 | 含义 |
|---|---|
| `second_name` | 姓氏单字，主键 |
| `slug` | URL 标识（拼音），全站唯一 |
| `pinyin` / `initial` | 拼音与首字母，用于搜索和 A–Z 导航 |
| `aliases` | 别名，逗号分隔存储 |
| `summary` | 列表卡片摘要 |
| `base_information` / `ori` / `mig` / `dis` / `cul` / `fam` | 纯文本资料字段，模板默认转义 |
| `keywords` | 词云数据，`value` 为 1–100 的展示权重 |
| `source_note` | 该条目的来源与性质说明 |
| `is_demo` | 是否为演示整理内容 |
| `is_featured` / `popularity` | 首页精选与排序权重，由数据显式指定 |
| `distribution.intensity` | 0–100 示意强度，非占比 |
| `relation_type` | `origin` 源出 / `branch` 分支 / `changed` 改姓 / `same_clan` 同源 |

关系记录必须恰好指向一个目标：`target_surname`（姓氏）或 `target_clan`（宗族），由数据库 `CheckConstraint` 保证。

## 校验与重新生成

```bash
# 修改原始文本后重新生成 catalog（确定性）
python scripts/generate_catalog.py

# 校验结构、引用、来源说明、HTML 标记与数量
python manage.py validate_catalog

# 写入数据库（幂等；--dry-run 只看统计）
python manage.py load_catalog

# 开发环境演示数据：省份、朝代元数据、账号、评论、收藏、历史
python manage.py seed_demo
```

### 校验规则（摘要）

- 姓氏数量 ≥ 32（当前 33）；`second_name`、`slug` 唯一。
- `pinyin`、`initial`、`summary`、各资料字段与 `source_note` 非空。
- `is_demo=True` 的记录必须提供 `source_note`，人物/事件/关系同样适用。
- 省份、朝代、目标姓氏、目标宗族必须存在于允许列表或同一文件。
- `intensity`、`keywords[].value` 为 0–100 / 1–100 的整数。
- 禁止 `<script`、`onerror=`、`javascript:` 等标记片段（纯文本策略）。
- 加载先校验后写入，整体在 `transaction.atomic()` 中执行；默认不删除文件外的既有记录，`--prune` 才清理。

校验失败会列出具体路径（如 `surnames[12].figures[1]: source_note 不能为空`），不会部分写库。

## 修改数据时的约定

1. 优先改 `data/surnames/` 原始文本或 `scripts/generate_catalog.py` 中的元数据，再重新生成；不要手改数据库。
2. 新增姓氏时同时补：摘要、8–12 个关键词、6–10 个省份强度、3–5 位人物、2–3 条迁徙事件、至少 1 条关系，以及每条记录的 `source_note`。
3. 不写入 HTML、脚本或外部图片链接；所有内容按纯文本展示。
4. 不引入受版权保护的整段原文；概述性资料可以，但需能说明来源。
5. 修改后运行 `validate_catalog`、`load_catalog` 与完整测试。

## 已知限制

- 只有 33 个姓氏，不能代表中国姓氏全貌；
- 人物与事件是概述性演示数据，未逐条核对史料；
- 分布强度是示意值，页面不得将其表述为统计比例；
- 港澳台数据仅作为地图完整性占位，不代表统计口径；
- 未提供数据版本迁移工具；结构变更时重新生成并加载 catalog 即可。
