# 部署到 PythonAnywhere（免费版）

本文把氏源完整部署到 PythonAnywhere 免费子域名：Django、登录、评论、收藏、历史、API 与 admin 都可用，SQLite 数据存放在持久磁盘。命令中的 `<pa-user>` 替换为你的 PythonAnywhere 用户名；**不要把 secret、管理员密码或 `~/.shiyuan.env` 的内容贴到聊天、截图或 issue 中**。

## 1. 为什么不是 GitHub Pages

氏源是 Django 服务端渲染的全栈站点。登录、评论、收藏、历史、API 和 admin 都依赖 Python 进程与数据库；GitHub Pages 只托管静态文件，`github.io/<repo>` 只能放静态快照，会失去这些功能。因此完整部署需要能运行 Python 与 SQLite 的主机。免费方案使用 PythonAnywhere 的 `https://<pa-user>.pythonanywhere.com` 子域名。

## 2. 免费版限制（2026-10）

- 1 个 web app、1 个 worker；
- **web app 1 个月到期**：Web tab 点 “Run until 1 month from today” 续期；到期文件不删除，续期即恢复；
- 512 MiB 磁盘；SQLite 数据库与 `staticfiles/` 都放在持久磁盘；
- 100 CPU 秒/天，只计控制台与计划任务（web app 请求不计）；首次加载 6,000+ 人物可能较慢；
- 免费子域名，不支持自定义域名；新免费账号没有 MySQL 与计划任务；
- 平台的安全设置里打开 **Force HTTPS**（对静态文件也生效）。

## 3. 首次部署前检查

1. 在当前网络执行：
   ```bash
   curl -sSI https://www.pythonanywhere.com/ | head -1
   ```
   若无法访问或极慢，先停下评估替代主机（付费 VPS / 国内云）；GitHub Pages 仍然不可行。
2. 注册/登录免费账号，记下用户名 `<pa-user>`。
3. 在 Account 页确认 System image 为 `innit`；在 Bash console 执行：
   ```bash
   python3.13 --version
   ```
   若只有 3.12，执行 `ls /usr/bin/python3.*` 选 3.12，并在 Web tab 保持一致。

## 4. 获取代码与虚拟环境

在 Bash console：

```bash
cd ~
git clone https://github.com/ningbojian/shiyuan.git
cd shiyuan
git log --oneline -1

mkvirtualenv --python=/usr/bin/python3.13 shiyuan-venv   # 只有 3.12 时替换路径
workon shiyuan-venv
python --version
pip install -r requirements.txt
```

期望：HEAD 为 `main` 的最新 commit；Django 5.2 安装成功。`requirements.txt` 已包含 WhiteNoise 与 pypinyin；生产不需要 gunicorn（WSGI 由平台托管）。

## 5. Web tab 配置

1. **Add a new web app** → **Manual Configuration** → Python 3.13（或 3.12）。
2. **Code**：
   - Source code：`/home/<pa-user>/shiyuan`
   - Working directory：`/home/<pa-user>/shiyuan`
3. **Virtualenv**：填 `shiyuan-venv`（或完整路径 `/home/<pa-user>/.virtualenvs/shiyuan-venv`）。
4. **WSGI configuration file**：打开平台生成的
   `/var/www/<pa-user>_pythonanywhere_com_wsgi.py`，用 [`deploy/pythonanywhere_wsgi.py`](../deploy/pythonanywhere_wsgi.py)
   的内容替换，并把 `YOUR_USERNAME` 改为 `<pa-user>`。该模板会读取 `~/.shiyuan.env` 并设置 `DJANGO_SETTINGS_MODULE`；不要改仓库里的 `project/wsgi.py`。
5. **Static files**：新增映射
   - URL：`/static/`
   - Directory：`/home/<pa-user>/shiyuan/staticfiles`
6. **Security**：打开 **Force HTTPS**。

完成后先不要点 Reload，继续创建环境文件。

## 6. 服务器环境变量

在 Bash console 创建 `~/.shiyuan.env`（secret 只存在于服务器，权限 600）：

```bash
cd ~
umask 077
PA_USERNAME=<pa-user>
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
printf '%s\n' \
  "DJANGO_DEBUG=0" \
  "DJANGO_SECRET_KEY=$SECRET_KEY" \
  "DJANGO_ALLOWED_HOSTS=$PA_USERNAME.pythonanywhere.com" \
  "DJANGO_CSRF_TRUSTED_ORIGINS=https://$PA_USERNAME.pythonanywhere.com" \
  "DJANGO_SECURE_SSL=0" \
  "DJANGO_TRUST_X_FORWARDED_PROTO=0" \
  > ~/.shiyuan.env
chmod 600 ~/.shiyuan.env
```

说明：

- 默认由平台 Force HTTPS 负责跳转；`DJANGO_SECURE_SSL=0` 与 `DJANGO_TRUST_X_FORWARDED_PROTO=0` 避免未知代理头导致重定向循环。
- 不要把该文件提交到 git；不要公开 `cat` 输出。
- 修改后需要 Web tab Reload 才生效。

## 7. 初始化数据

在 Bash console（同一虚拟环境）：

```bash
cd ~/shiyuan
set -a; source ~/.shiyuan.env; set +a
workon shiyuan-venv

python manage.py check
python manage.py check --deploy   # 默认 SSL 关闭时预期 W004/W008/W012/W016
python manage.py migrate
python manage.py load_catalog --dry-run   # 只校验/统计，不写库；应显示 348 姓氏 / 6251 人物
python manage.py seed_demo --force        # 内部调用 load_catalog，加载 348 姓氏与示例内容
```

`check --deploy` 的 4 个警告来自平台 HTTPS 模式下的默认取舍（未开启 HSTS/Secure Cookie/SSL 跳转），不是部署失败。若出现 `ALLOWED_HOSTS`/`CSRF` 相关错误，先修 `~/.shiyuan.env`，不要用 `DEBUG=1` 绕过。

首次演示数据创建后，立即轮换三个演示账号密码（不打印密码）：

```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; import secrets; U=get_user_model(); users=list(U.objects.filter(username__in=['demo','reader1','reader2'])); [u.set_password(secrets.token_urlsafe(24)) or u.save(update_fields=['password']) for u in users]; print(f'demo passwords rotated: {len(users)}')"
```

创建管理员（使用非常见用户名 + 强密码；不要把密码发给任何人）：

```bash
python manage.py createsuperuser
```

收集静态文件：

```bash
python manage.py collectstatic --noinput
```

完成后 Web tab 点 **Reload**；首次访问可能较慢。

## 8. 验收

```bash
curl -sSI https://<pa-user>.pythonanywhere.com/ | head -1          # 200
curl -sSI http://<pa-user>.pythonanywhere.com/ | head -3           # 301/302 到 https
curl -sSIL https://<pa-user>.pythonanywhere.com/ | head -20        # 无循环
curl -sSI https://<pa-user>.pythonanywhere.com/ | grep -Ei 'x-content-type|x-frame|referrer|strict-transport'
curl -sS https://<pa-user>.pythonanywhere.com/ | grep -o 'rel="canonical" href="[^"]*"'
```

实测平台默认环境下 canonical 已为 `https://`；由于 `DJANGO_SECURE_SSL=0`，仍没有 HSTS/Secure Cookie，这是平台 HTTPS 模式的已知取舍。若要补齐这两项，再做下面的可选实验。

浏览器走查：

- `/`、`/surname/`、`/surname/li/`、`/surname/wan/`（原始资料条目）、`/surname/deng/`（无人物条目）、`/surname/you/`、`/surname/figures/`、`/surname/origins/`、`/user/register/`、`/user/login/` 均 200；
- 详情页四张图与文本替代表可见；`/surname/wan/` 显示“课程原始资料”徽章，`/surname/li/` 显示整理正文与合并后的人物；
- 从首页 HTML 取一个 `/static/...` URL 并 curl → 200；admin CSS → 200；
- `/api/v1/surnames/`（`count=348`）、`/api/v1/surnames/li/`、`/api/v1/meta/`、`/sitemap.xml`、`/robots.txt` 均正常；
- 注册新账号 → 登录 → 收藏 → 历史 → 评论 → 改密 → POST 退出；管理员登录 `/admin/`；确认 `demo`/`reader1` 旧密码不能再登录；
- 写入评论后 Web tab Reload，刷新页面评论仍在（SQLite 在 `/home/<pa-user>/shiyuan/db.sqlite3`）；
- 移动端 375px 与夜间模式抽查；Web tab → Error log 无 traceback。

### 可选：在 Django 层开启 HTTPS 感知

平台 Force HTTPS 已能完成跳转。若希望 canonical 使用 https 并获得 HSTS/Secure Cookie：

```bash
# 先只信任代理头，验证 canonical 变为 https
sed -i 's/^DJANGO_TRUST_X_FORWARDED_PROTO=0/DJANGO_TRUST_X_FORWARDED_PROTO=1/' ~/.shiyuan.env
# Reload 后
curl -sS https://<pa-user>.pythonanywhere.com/ | grep -o 'rel="canonical" href="[^"]*"'

# canonical 正确后再开启 SSL 跳转
sed -i 's/^DJANGO_SECURE_SSL=0/DJANGO_SECURE_SSL=1/' ~/.shiyuan.env
# Reload 后
curl -sSI https://<pa-user>.pythonanywhere.com/ | head -1
curl -sSI http://<pa-user>.pythonanywhere.com/ | head -3
```

若出现重定向循环或 canonical 仍为 `http://`，立即把两个变量都改回 `0` 并 Reload；用无痕窗口清缓存再试。开启 `DJANGO_SECURE_SSL=1` 后，`check --deploy` 应为 0 警告。

## 9. 更新流程

```bash
cd ~/shiyuan
# 1) 先备份（见下一节）
python -c "import sqlite3; from pathlib import Path; from datetime import datetime; src=sqlite3.connect(Path.home()/'shiyuan'/'db.sqlite3'); dst=sqlite3.connect(Path.home()/'backups'/f'db-{datetime.now():%Y%m%d-%H%M%S}.sqlite3'); src.backup(dst); dst.commit(); dst.close(); src.close(); print('backup done')"

# 2) 更新代码与依赖
git pull --ff-only
workon shiyuan-venv
pip install -r requirements.txt

# 3) 迁移、加载、静态文件
set -a; source ~/.shiyuan.env; set +a
python manage.py migrate
python manage.py load_catalog
python manage.py collectstatic --noinput
```

最后在 Web tab 点 Reload。若 `git pull --ff-only` 失败，先查看 `git status`，不要 force-push 或强拉覆盖本地数据。

## 10. 备份与回滚

**备份数据库**（使用 SQLite backup API，避免写入时直接 `cp`）：

```bash
mkdir -p ~/backups
python -c "import sqlite3; from pathlib import Path; from datetime import datetime; src=sqlite3.connect(Path.home()/'shiyuan'/'db.sqlite3'); dst=sqlite3.connect(Path.home()/'backups'/f'db-{datetime.now():%Y%m%d-%H%M%S}.sqlite3'); src.backup(dst); dst.commit(); dst.close(); src.close(); print('backup done')"
ls -lh ~/backups
```

通过 Files tab 下载一份到本地。建议每次更新前备份。

**回滚代码**：

```bash
cd ~/shiyuan
git log --oneline -5
git checkout <上一个正常 commit>       # 或已推送的 tag，如 deploy-2026-10-20
# Reload
```

回滚后如数据库 schema 已前进，按备份恢复：

```bash
# 先停写（或直接 Reload 前操作），再用备份覆盖
cp ~/backups/db-<timestamp>.sqlite3 ~/shiyuan/db.sqlite3
```

同时备份 `~/.shiyuan.env` 与平台的 WSGI 文件；它们不在 git 中。

## 11. 故障排查

| 现象 | 检查 |
|---|---|
| 502 / 无法访问 | Web tab Error log；WSGI 文件路径与 `PA_USERNAME`；虚拟环境是否正确；`pip install` 是否完成 |
| 400 Bad Request | `DJANGO_ALLOWED_HOSTS` 是否包含 `<pa-user>.pythonanywhere.com`；是否多/少了空格 |
| 403 CSRF | `DJANGO_CSRF_TRUSTED_ORIGINS` 是否为 `https://<pa-user>.pythonanywhere.com`；Force HTTPS 是否开启 |
| 页面无样式 / 静态 404 | `collectstatic --noinput` 是否执行；`/static/` → `/home/<pa-user>/shiyuan/staticfiles` 映射是否正确 |
| 所有 HTML 500，但 API/sitemap/robots 200 | 通常是未执行 `collectstatic`，模板里的 `{% static %}` 找不到 manifest；运行 `collectstatic --noinput` 后点 Reload |
| 重定向循环 | 把 `DJANGO_SECURE_SSL` 与 `DJANGO_TRUST_X_FORWARDED_PROTO` 都设为 `0`，Reload，用无痕窗口重试 |
| 页面显示旧内容 | Web tab Reload；确认 `git log` 是预期 commit；清浏览器缓存 |
| 到期后站点停用 | Web tab 点 “Run until 1 month from today” 续期 |
| 首次加载很慢 / CPU 超限 | 只执行一次 `seed_demo --force`；若仍超限，改用本地生成数据库后上传，或与维护者讨论批量优化 |

日志位置：Web tab → **Error log**（应用 traceback）与 **Server log**（访问日志）。

## 12. 安全与限制

- 生产必须 `DJANGO_DEBUG=0`；缺少 `DJANGO_SECRET_KEY` 会直接报错。
- secret、管理员密码、`~/.shiyuan.env` 不进入仓库、不截图、不发聊天；泄漏后重新生成 secret 并 Reload（会话失效，密码不变）。
- 免费版为单 worker，SQLite 适合当前 348 姓氏 / 6,251 人物 / 读多写少的规模；多 worker、高并发写或全文检索时需迁移 PostgreSQL。
- 免费子域名不支持自定义域名；中国大陆访问速度可能不稳定，必要时评估付费 VPS/国内云。GitHub Pages 仍不能运行 Django。
- 演示账号密码在首次部署后立即轮换；不要在生产保留 `demo123456`。
