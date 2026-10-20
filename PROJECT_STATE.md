# 项目状态

最后更新：2026-10-20

## 当前阶段

**Phase 7 完成：课程原始数据已入库；Phase 6 公网部署待执行。** 348 个姓氏、6,251 位人物已在本地库验证；升级代码已提交到 `feature/shiyuan-upgrade`，下一步是 PythonAnywhere 部署与公网验收。

## 已完成

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 环境化密钥、内置 auth、Profile、注册/登录/退出/改密、评论所有权、移除 pyecharts/pickle/CDN/`\|safe`、CI 骨架 | 完成 |
| Phase 2 | 新 schema（FK + 约束 + 索引）、33 个姓氏 catalog、加载/校验/seed 命令、数据说明 | 完成 |
| Phase 3 | 纸墨设计系统、首页/目录/搜索、详情 TOC、四类本地 ECharts + 文本替代表、静态页收口、移动端/夜间模式 | 完成 |
| Phase 4 | 人物索引与详情、源流关系图、收藏/历史（保留 50 条）、个人中心、只读 API v1、登录/评论限流与审计日志 | 完成 |
| Phase 5 | 部署检查、静态长缓存、sitemap/robots/canonical/OG/JSON-LD、404/500、无障碍与响应式验收、README/QA/项目状态、CI collectstatic | 完成 |
| Phase 6 | PythonAnywhere 免费部署模板、部署文档、合并 main、公网验收 | 部署中 |
| Phase 7 | 课程归档解析器、315 个原始条目、6,251 位人物、`is_imported` 来源标记与原始资料 UI、22 个时期 | 完成 |

## 当前验证结果

- 自动化测试：219 个，全部通过（最终验收命令见下）；
- `ruff check .`：通过；
- `python manage.py check --deploy`（生产环境变量 + `DJANGO_SECURE_SSL=1`）：无问题；
- `collectstatic --noinput`（生产 manifest storage）：通过；
- Lighthouse Accessibility：5 个页面均为 1.00；
- 响应式：375/768/1440 px 共 18 次检查无横向溢出；
- 最终独立审查：0 Critical；4 Important（反向代理 HTTPS、生产 gunicorn、审计日志、关键词空状态）已修复并由测试钉住；11 Minor 记录为后续优化；
- 数据规模：348 姓氏（33 整理 + 315 课程原始资料）/ 6,251 人物 / 66 迁徙事件 / 36 源流关系 / 10 宗族 / 22 个时期。

```bash
DJANGO_DEBUG=1 python manage.py test -v 2
ruff check .
DJANGO_DEBUG=1 python manage.py check
```

## 已知限制

1. **SQLite 单机**：348 姓氏 / 6,251 人物 / 单 worker 的读多写少场景足够，无需数据库服务器；多 worker、持续高并发写、全文检索或平台磁盘非持久时，切换 PostgreSQL 并重新评估缓存与限流。
2. **数据性质不同**：315 个条目来自课程原始资料（`is_imported=True`，未校订，部分只有文字而没有结构化分布/迁徙/关系）；33 个整理条目的正文、人物、迁徙与分布为演示整理内容，分布强度为示意值。
3. **评论无分页**：详情页一次加载该姓氏全部可见评论；当前数据量很小，评论量增长后应加分页或“加载更多”。
4. **搜索为 `icontains`**：348 个姓氏足够；数据量继续增大后可引入 SQLite FTS 或 PostgreSQL 全文检索。
5. **API 无认证/限流**：只读公开接口，部署到公网前建议在网关层加限流与缓存。
6. **未实现找回密码/邮箱验证**：当前账号体系只覆盖注册、登录、资料与密码修改。
7. **未提供 Docker**：验收环境没有 Docker，部署文档给出 gunicorn + WhiteNoise + 环境变量路径。
8. **整页缓存未启用**：页头包含登录态与 CSRF 表单，整页 `cache_page` 可能跨用户串页；当前以查询预算与静态资源长缓存为主。

## 下一步（可选增强）

1. 姓氏对比页（`/surname/compare/?names=li,wang`），复用详情页图表 payload；
2. 打印样式与“导出 JSON/PDF”；
3. PWA/service worker，离线阅读最近浏览；
4. 管理后台数据看板：缺人物、缺来源、待校验记录；
5. 把 `docs/API.md` 渲染为公开的 `/api/` 文档页；
6. 评论分页与举报/审核队列；
7. PostgreSQL + Redis 缓存/限流，配套部署模板与备份策略；
8. 密码找回与邮箱验证。

## 发布前检查

- [x] 348 个姓氏详情页可访问，缺失数据有空状态；
- [x] 本地库计数：348 姓氏 / 315 原始条目 / 6,251 人物 / 22 时期；
- [x] XSS、CSRF、IDOR、限流测试通过；
- [x] `check --deploy` 无警告（安全环境变量齐全时）；
- [x] 无外部 CDN/字体/图表依赖；
- [x] 404/500 模板与 robots/sitemap；
- [x] README、API、DATA、QA、项目报告一致；
- [ ] PythonAnywhere 部署、HTTPS 与备份策略（Phase 6）；
- [ ] 公网验收后记录在线 URL 与部署日期。
