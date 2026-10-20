# 项目状态

最后更新：2026-10-20

## 当前阶段

**Phase 5 收尾：可发布状态。** 功能、数据、安全、测试、SEO、无障碍与部署文档均已完成；尚未执行 git commit（等待确认）。

## 已完成

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 环境化密钥、内置 auth、Profile、注册/登录/退出/改密、评论所有权、移除 pyecharts/pickle/CDN/`\|safe`、CI 骨架 | 完成 |
| Phase 2 | 新 schema（FK + 约束 + 索引）、33 个姓氏 catalog、加载/校验/seed 命令、数据说明 | 完成 |
| Phase 3 | 纸墨设计系统、首页/目录/搜索、详情 TOC、四类本地 ECharts + 文本替代表、静态页收口、移动端/夜间模式 | 完成 |
| Phase 4 | 人物索引与详情、源流关系图、收藏/历史（保留 50 条）、个人中心、只读 API v1、登录/评论限流与审计日志 | 完成 |
| Phase 5 | 部署检查、静态长缓存、sitemap/robots/canonical/OG/JSON-LD、404/500、无障碍与响应式验收、README/QA/项目状态、CI collectstatic | 完成 |

## 当前验证结果

- 自动化测试：189 个，全部通过（最终验收命令见下）；
- `ruff check .`：通过；
- `python manage.py check --deploy`（生产环境变量 + `DJANGO_SECURE_SSL=1`）：无问题；
- `collectstatic --noinput`（生产 manifest storage）：通过；
- Lighthouse Accessibility：5 个页面均为 1.00；
- 响应式：375/768/1440 px 共 18 次检查无横向溢出；
- 最终独立审查：0 Critical；4 Important（反向代理 HTTPS、生产 gunicorn、审计日志、关键词空状态）已修复并由测试钉住；11 Minor 记录为后续优化；
- 数据规模：33 姓氏 / 132 人物 / 66 迁徙事件 / 36 源流关系 / 10 宗族。

```bash
DJANGO_DEBUG=1 python manage.py test -v 2
ruff check .
DJANGO_DEBUG=1 python manage.py check
```

## 已知限制

1. **SQLite 单机**：适合课程演示；多实例部署需切换数据库并重新评估并发写入、缓存与限流。
2. **演示数据**：29 个扩展姓氏与全部人物/迁徙/分布文本为整理内容，不是学术统计；分布强度为示意值。
3. **评论无分页**：详情页一次加载该姓氏全部可见评论；当前数据量很小，评论量增长后应加分页或“加载更多”。
4. **搜索为 `icontains`**：33 个姓氏足够；数据量增大后可引入 SQLite FTS 或 PostgreSQL 全文检索。
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

- [x] 33 个姓氏详情页可访问，缺失数据有空状态；
- [x] XSS、CSRF、IDOR、限流测试通过；
- [x] `check --deploy` 无警告（安全环境变量齐全时）；
- [x] 无外部 CDN/字体/图表依赖；
- [x] 404/500 模板与 robots/sitemap；
- [x] README、API、DATA、QA、项目报告一致；
- [ ] git commit（等待用户确认）；
- [ ] 实际公网域名、HTTPS 与备份策略（部署时配置）。
