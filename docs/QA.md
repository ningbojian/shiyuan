# 无障碍与响应式验收

验收日期：2026-10-20。环境：Windows 11、Python 3.13、Django 5.2、Chrome（headless）、Lighthouse 13.5.0。

## 自动化结果

| 检查 | 范围 | 结果 |
|---|---|---|
| Lighthouse Accessibility | `/`、`/surname/li/`、`/surname/figures/`、`/surname/origins/`、`/user/login/` | 5/5 页得分 **1.00**，无失败审计项 |
| 横向溢出 | 上述 5 页 + `/surname/`，375 / 768 / 1440 px | 18 次检查均为 `scrollWidth - clientWidth = 0` |
| 图表初始化 | `/surname/li/` 的分布、迁徙、关系、词云 | canvas 数量 1 / 2 / 1 / 1，尺寸正常；夜间模式重绘后仍为 5 个 canvas |
| 控制台错误 | 详情页与首页 | 无 JS 错误、无 404 资源；已补 `rel="icon"` 避免默认 favicon 请求 |
| 键盘焦点 | Tab 进入表单控件 | `:focus-visible` 生效，3px 实线轮廓 |
| 移动导航 | 375 px 点击“菜单” | `aria-expanded` 由 `false` 变为 `true` |
| 颜色对比度 | 纸墨/夜间主色与次要文本 | 见下表，均达到 WCAG AA；主文本达到 AAA |

### 对比度

| 组合 | 比值 | 要求 |
|---|---|---|
| 主文本 `--ink` / `--paper` | 11.19:1 | AAA（≥ 7:1） |
| 次要文本 `--muted` / `--paper` | 4.96:1 | AA（≥ 4.5:1） |
| 次要文本 `--muted` / `--paper-deep` | 4.54:1 | AA（≥ 4.5:1） |
| 夜间次要文本 `--muted` / `--paper` | 7.70:1 | AAA |

次要文本原为 `#6f7568`（4.22:1），本轮已调整为 `#646a5d`，并由 `Surname/tests/test_accessibility.py` 固定回归。

## 已人工确认的无障碍实现

- 全站 skip link、`main` 焦点目标、语义化 `header/nav/main/footer`。
- 当前导航与面包屑使用 `aria-current`；导航折叠按钮维护 `aria-expanded`，Esc 可关闭并归还焦点。
- 主题按钮维护 `aria-pressed` 与动态 `aria-label`；主题选择写入 `localStorage`。
- 所有表单控件有显式 `<label for>`；错误信息使用 `role="alert"`。
- 四类图表均提供 `role="img"` 容器、`aria-label` 和始终存在的 `<details>` 数据表；图表初始化失败时词云回退为文字列表。
- `prefers-reduced-motion: reduce` 关闭过渡与迁徙路线动画；`prefers-color-scheme` 作为首次访问的主题默认值。
- 无外部字体、CDN 或第三方脚本；断网后已加载页面仍使用本地 CSS/JS。

## 复现命令

```bash
DJANGO_DEBUG=1 python manage.py runserver 127.0.0.1:8000

CHROME_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe" \
npx lighthouse http://127.0.0.1:8000/ \
  --only-categories=accessibility \
  --chrome-flags="--headless=new --no-sandbox" \
  --output=json --output-path=lighthouse-home.json
```

响应式与图表检查使用 Playwright（复用本机 Chrome）在 375/768/1440 三种视口下读取 `scrollWidth`，并逐块滚动触发 ECharts 懒加载。

## 已知限制

- 未做真实屏幕阅读器（NVDA/VoiceOver）人工走查；Lighthouse 使用 axe-core 子集，不能替代人工语义检查。
- 移动导航与主题切换依赖 JavaScript；禁用 JS 时导航仍可通过页脚链接到达，但折叠菜单与主题选择不可用。
- 图表为 CDN 无关的本地 ECharts，首次进入图表区域时加载（IntersectionObserver），低端设备可能有一帧延迟。
- 演示数据中的分布强度是 0–100 的示意值，不是人口统计；页面与数据表均已标注。
