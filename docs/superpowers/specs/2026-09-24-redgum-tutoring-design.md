# Redgum Tutoring 排课与课时跟踪系统 — 设计文档

- 课程:ISYS3001 Managing Software Development · Case Study 3
- 项目路径:`~/redgum-tutoring`
- 日期:2026-09-24
- 状态:已确认(待实施)

---

## 1. 背景与目标

Redgum Tutoring 是 Ipswich 的一家课后辅导中心(约 140 名在读学生、11 名导师),排课依赖一块磁力白板、一本铅笔日记簿和一块导师信息软木板。已经出现的问题:同一房间双订、导师中途离职后 9 名学生周末靠记忆重新分配、导师为已取消的课时白跑、清洁工擦掉白板导致半周课表丢失。Helen 估计每周因空缺、失误和缺席损失 4–7 个付费小时,超过房租。

本系统目标(案例第 3 节):

1. 一个地方保存学生、导师和课时,让前台 **一分钟内** 完成一次正确预约;
2. 用单一课表替代日记簿、白板和软木板,前台与导师都依赖它;
3. 确保**任何课时都落在该导师的可用时段内**(当前事故的主要根源)。

**本系统替换的是日记簿、白板和软木板,不替换发票、会计,也不替代 Helen 对"谁教谁"的判断。**

---

## 2. 范围

### 2.1 Sprint 内(10 个故事)

| # | 分支 | 故事 | 关键验收 |
|---|------|------|---------|
| 1 | `story/01-foundation` | 项目骨架与数据模型 | FastAPI 可启动;SQLite 建表;5 个模型;基础模板与静态资源;空库可运行 |
| 2 | `story/02-auth` | 登录与角色 | `username`+密码登录(会话 cookie);ADMIN/TUTOR 两种角色;未登录跳转登录页;导师不能访问管理页面 |
| 3 | `story/03-students` | 管理员维护学生 | 新增(姓名/年级/家长联系方式必填,缺哪项报哪项)、查询(按姓名/年级搜索)、编辑、停用/启用 |
| 4 | `story/04-tutors` | 管理员维护导师 | 新增(姓名+科目)、编辑、停用/启用;**停用导师不出现在排课下拉中**;保留历史课时 |
| 5 | `story/05-availability` | 管理员维护可用时段 | 为导师增/改/删可用时段(星期几+起止时间);同一导师多条;界面展示清晰 |
| 6 | `story/06-book-session` | 排课(**核心领域逻辑**) | 选择学生/导师/科目/日期/开始时间/时长(60/90);**必须完整落在导师当天某可用时段内**,否则拒绝并说明原因;新课时状态 BOOKED |
| 7 | `story/07-manage-session` | 改期/取消/状态流转 | 改日期或开始时间(同样校验可用时段)、取消、标记出席/缺席;取消后仍可见;互不影响 |
| 8 | `story/08-schedule` | 课表与学生历史 | 管理员按**日/周**查看课表(可按导师筛选);某学生**过去+未来**课时可列出 |
| 9 | `story/09-tutor-view` | 导师视图 | 导师看到**自己的**即将到来课时(学生、日期、时间、科目);**看不到别人的**;无课时显示空列表而非报错 |
| 10 | `story/10-delivery` | 交付 | 种子数据(案例文档原值);README 干净环境可跑;`pytest` 全绿;交接文档与 Jira CSV |

### 2.2 明确不做(进产品 Backlog,交接文档写明原因)

房间分配与房间冲突检测;重复预约/时间重叠检测(**案例明确排除**);发票、费用、预付包、支付;导师工时表与工资;短信/邮件提醒;家长门户与自助预约;视频课时链接;蓝卡与合规到期跟踪;会计报告/Xero 集成;一月强化班;NAPLAN 工作坊;披萨夜;学期内整周不可用(如 Tomás 第 8 周);"三周未预约学生"报告;导师周课时上限(8 节)。

---

## 3. 技术选型与决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 语言/框架 | **Python 3.10+ + FastAPI** | 文件量小;案例明确允许任意 web 应用;团队可读 |
| 页面渲染 | **Jinja2 服务端渲染** | 无需前后端分离、无 Node/构建步骤,前台表单场景最合适 |
| 数据库 | **SQLite 文件**(`redgum.db`)+ SQLAlchemy 2.x | 零安装;ORM 可测试;重启不丢数据 |
| 认证 | **Starlette SessionMiddleware 签名 cookie** + `bcrypt` 密码哈希 | 服务端渲染天然适配;无 token 存储问题 |
| 表单处理 | FastAPI `Form()` + 显式校验辅助函数 | 错误信息可控、可读;不引入额外表单库 |
| 消息提示 | PRG(Post/Redirect/Get)+ 会话 flash | 避免重复提交;模板统一渲染 |
| 列表 | 搜索/筛选,不做分页 | 规模(140 学生/11 导师)不需要;分页进 backlog |
| 样式 | 本地 vendored 单文件 CSS | 演示不依赖 CDN/网络 |
| 测试 | pytest + FastAPI TestClient,内存 SQLite | 依赖少、样板少 |
| 运行 | `pip install -r requirements.txt` + `uvicorn` | README 三行;老师只需 Python |

**依赖清单(全部):** `fastapi`、`uvicorn[standard]`、`jinja2`、`sqlalchemy`、`bcrypt`、`python-multipart`(表单)、`itsdangerous`(会话签名);测试:`pytest`、`httpx`。

**开发环境说明:** 本机系统 Python 为 3.9(EOL),开发使用 `uv` 安装的 Python 3.12 虚拟环境;代码保持 **3.10+ 兼容**,README 要求 Python 3.10+。

---

## 4. 架构与项目结构

```
redgum-tutoring/
├── app/
│   ├── main.py              # FastAPI 应用、启动建表+种子、路由注册、异常处理
│   ├── db.py                # engine / SessionLocal / get_db / init_db
│   ├── models.py            # Student, Tutor, AvailabilityWindow, Session, AppUser
│   ├── security.py          # 密码哈希、登录/登出、current_user、require_admin
│   ├── errors.py            # DomainError(校验失败 → 表单错误/提示)
│   ├── services/
│   │   ├── students.py      # 学生 CRUD + 搜索
│   │   ├── tutors.py        # 导师 CRUD + 可排课导师列表
│   │   ├── availability.py  # 可用时段增改删
│   │   ├── sessions.py      # 排课/改期/取消/状态 + 可用时段校验调用
│   │   └── schedule.py      # 日/周课表、学生历史、导师即将到来
│   ├── routers/
│   │   ├── auth.py          # /login /logout
│   │   ├── students.py      # /students*
│   │   ├── tutors.py        # /tutors* /tutors/{id}/availability
│   │   ├── sessions.py      # /sessions*
│   │   └── views.py         # /schedule /my-sessions /
│   ├── seed.py              # 种子数据(仅空库写入;启动时调用)
│   ├── templates/           # base.html + 各页面(含 _form 片段与错误块)
│   └── static/style.css     # 本地样式
├── tests/                   # pytest(见第 10 节)
├── requirements.txt
├── README.md
├── .gitignore
└── docs/
    ├── superpowers/specs/   # 本文档
    ├── superpowers/plans/   # 实施计划
    ├── handover.md          # 交接文档(案例第 9 节六部分)
    └── jira-import.csv      # Jira 导入用 backlog
```

---

## 5. 数据模型

SQLite;时间字段用 `Date`/`Time`(SQLAlchemy),金额无关(本项目不涉及收费)。所有表含 `created_at`、`updated_at`。

### student
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(100) | NOT NULL | |
| year_level | Integer | NOT NULL | 5–12 |
| school | String(120) | NULL | 报名表有此项 |
| contact_name | String(100) | NOT NULL | 家长/监护人姓名 |
| contact_phone | String(20) | NOT NULL | |
| contact_email | String(120) | NULL | |
| subjects | String(200) | NULL | 想学的科目(自由文本) |
| status | String(20) | NOT NULL | `ACTIVE` / `INACTIVE` |

### tutor
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| name | String(100) | NOT NULL | |
| phone | String(20) | NULL | |
| subjects | String(200) | NOT NULL | 教授的科目,如 "Physics 10-12, Chemistry 10-12" |
| status | String(20) | NOT NULL | `ACTIVE` / `INACTIVE` |

### availability_window
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| tutor_id | Integer | NOT NULL, FK → tutor | |
| day_of_week | String(10) | NOT NULL | `TUESDAY` … `SATURDAY`(中心仅周二–周六开放) |
| start_time | Time | NOT NULL | |
| end_time | Time | NOT NULL | 必须晚于 start_time |

同一导师同一天可有多条不重叠窗口(重叠不检测,案例排除冲突检测)。

### session
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| student_id | Integer | NOT NULL, FK | |
| tutor_id | Integer | NOT NULL, FK | |
| subject | String(100) | NOT NULL | 本次课时科目 |
| session_date | Date | NOT NULL | |
| start_time | Time | NOT NULL | |
| length_minutes | Integer | NOT NULL | 仅允许 60 / 90 |
| status | String(20) | NOT NULL | `BOOKED` / `ATTENDED` / `CANCELLED` / `MISSED` |

状态单向:`BOOKED → ATTENDED | MISSED | CANCELLED`;终态不可再变(取消/出席/缺席后不能再改期)。已取消课时保留记录、不物理删除。

### app_user
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | |
| username | String(50) | NOT NULL, UNIQUE | |
| password_hash | String(100) | NOT NULL | bcrypt |
| role | String(20) | NOT NULL | `ADMIN` / `TUTOR` |
| tutor_id | Integer | NULL, FK → tutor | TUTOR 角色必须关联;ADMIN 可空(Helen 也可关联以查看自己的课时) |
| status | String(20) | NOT NULL | `ACTIVE` / `INACTIVE` |

---

## 6. 领域规则(核心逻辑)

`services/sessions.py::validate_slot(tutor, session_date, start_time, length_minutes)`,在**排课和改期**时都必须调用:

1. `length_minutes ∈ {60, 90}`,否则拒绝;
2. 导师必须 `ACTIVE`(停用导师不可排课);
3. 新排课时学生必须 `ACTIVE`;
4. 由 `session_date` 推导星期几,取该导师**当天的全部可用窗口**:
   - 当天没有窗口 → 拒绝,提示"该导师周X没有可用时段";
   - 结束时间 = 开始时间 + 时长;**必须完整落在某一个窗口内**(`window.start ≤ start` 且 `end ≤ window.end`),否则拒绝,并列出当天窗口,例如:
     > Tomás 周二可用 15:30–19:00;18:30 开始的 60 分钟课时会到 19:30,超出窗口。
5. 校验通过才写入/更新;失败返回表单错误,不产生任何数据变更。

**不检测**课时之间、学生之间、导师之间的重叠(案例明确排除)。

---

## 7. 路由与页面

| 方法 | 路径 | 角色 | 说明 |
|------|------|------|------|
| GET/POST | `/login` | 公开 | 登录表单 / 提交 |
| POST | `/logout` | 登录 | 登出 |
| GET | `/` | 登录 | ADMIN → `/schedule`;TUTOR → `/my-sessions` |
| GET | `/students` | ADMIN | 列表 + 姓名/年级搜索 + 状态筛选 |
| GET/POST | `/students/new` | ADMIN | 新增(校验:姓名/年级/联系人必填) |
| GET/POST | `/students/{id}/edit` | ADMIN | 编辑 |
| POST | `/students/{id}/status` | ADMIN | 停用/启用 |
| GET | `/students/{id}/sessions` | ADMIN | 该学生**过去+未来**课时 |
| GET | `/tutors` | ADMIN | 列表 |
| GET/POST | `/tutors/new` | ADMIN | 新增(姓名+科目必填) |
| GET/POST | `/tutors/{id}/edit` | ADMIN | 编辑 |
| POST | `/tutors/{id}/status` | ADMIN | 停用/启用 |
| GET | `/tutors/{id}/availability` | ADMIN | 该导师可用时段列表 + 新增表单 |
| POST | `/tutors/{id}/availability` | ADMIN | 新增时段 |
| POST | `/availability/{id}/edit` | ADMIN | 修改时段 |
| POST | `/availability/{id}/delete` | ADMIN | 删除时段 |
| GET | `/sessions` | ADMIN | 列表 + 筛选(日期范围/导师/学生/状态) |
| GET/POST | `/sessions/new` | ADMIN | 排课(核心校验) |
| GET/POST | `/sessions/{id}/edit` | ADMIN | 改期(改日期/开始时间/时长,同样校验) |
| POST | `/sessions/{id}/cancel` | ADMIN | 取消 |
| POST | `/sessions/{id}/status` | ADMIN | 标记 ATTENDED / MISSED |
| GET | `/schedule` | ADMIN | `?date=&view=day|week&tutor_id=` 课表 |
| GET | `/my-sessions` | TUTOR | 自己的即将到来课时 |

所有 POST 成功后 302 重定向(PRG),失败时带错误信息重新渲染表单。

---

## 8. 认证与权限

- 登录:`username` + 密码(bcrypt 校验,`app_user.status = ACTIVE`);
- 会话:Starlette `SessionMiddleware`(签名 cookie,`secret_key` 在配置中有开发默认值);
- `require_admin` 依赖:非 ADMIN 访问管理路由 → **HTTP 403 简单错误页**(不重定向,便于测试与排查);
- TUTOR 只能访问 `/my-sessions`;数据查询以 `current_user.tutor_id` 过滤,不接受前端传入的 tutor_id;
- 已知限制(写交接文档):无 CSRF token(依赖 `SameSite=Lax`)、无登录失败限流、无密码找回。

---

## 9. 种子数据(案例文档原值)

`seed.py`:仅当库为空时写入(幂等)。

**导师与可用时段:**
| 导师 | 科目 | 可用时段 |
|------|------|---------|
| Tomás Ferreira | Physics 10–12, Chemistry 10–12, Maths Methods 11–12 | 周二 15:30–19:00;周三 15:30–18:00;周四 16:00–18:30;周六 09:00–12:30 |
| Helen Vasquez | Maths 5–12 | 周三 15:00–18:30;周六 09:00–13:00 |
| Priyanka Shah | Maths 5–10, Science 7–10 | 周二 16:00–19:00;周四 15:30–18:00 |
| Marcus Webb(已停用,演示) | English 7–10 | 周五 15:30–18:00 |

**学生:** Ella Nguyen(11,Physics)、Jayden Pike(10,Maths)、Sara Habib(12,Chemistry)、Oliver Brandt(9,Maths)、Mia Okafor(12,Maths Methods)、Kai Lombardo(11,Physics,S-0311)、Noah Fischer(8,Maths)。

**课时(文档 B 那一周,2026-08-11 至 08-15):** 按日记原样,状态映射 `A→ATTENDED`、`N→MISSED`、`C→CANCELLED`、`CL→CANCELLED`;其中周四 18:30 Jayden 一条按日记备注"已改到周六 9:00",**不作为课时写入**(种子数据本身即符合可用时段规则)。另动态生成**下周**若干 BOOKED 课时(相对当前日期计算),保证任何时间演示都有"即将到来"数据。

**账号:** `deb`(ADMIN)、`helen`(ADMIN,关联导师)、`tomas`(TUTOR,关联导师);密码统一 `redgum123`(README 注明为演示值)。

---

## 10. 测试策略

pytest + FastAPI `TestClient`;每个测试独立内存 SQLite(依赖覆盖 + `create_all`),种子不参与测试。

| 测试文件 | 覆盖故事 | 要点 |
|---------|---------|------|
| `test_availability_rule.py` | 6,7 | **纯单元**:恰好贴合、开始早于窗口、结束晚于窗口、当天无窗口、90 分钟放不下、时长非 60/90、停用导师、改期重校验 |
| `test_auth.py` | 2 | 登录成功/密码错/停用账号/登出;未登录重定向;TUTOR 访问管理页被拒 |
| `test_students.py` | 3 | 新增成功;缺姓名/年级/联系人分别报错且不落库;编辑;停用后不在可选列表;搜索 |
| `test_tutors.py` | 4 | 新增/编辑;停用后不出现在排课下拉;历史课时保留 |
| `test_availability.py` | 5 | 增/改/删;结束早于开始被拒;非管理员被拒 |
| `test_sessions.py` | 6,7 | 排课成功;各类越窗拒绝;改期重校验;取消后仍可见;标记出席/缺席;终态不可改;改一节不影响另一节 |
| `test_schedule.py` | 8,9 | 日/周课表;按导师筛选;学生过去+未来;导师只看自己的;无数据返回空列表 |

`pytest` 为 DoD 验收命令,README 写明。

---

## 11. 构建、运行与交付

**README 全部内容(干净环境):**
```bash
python3 -m venv .venv && source .venv/bin/activate   # 需要 Python 3.10+
pip install -r requirements.txt
uvicorn app.main:app --reload                        # http://localhost:8000
pytest                                               # 跑测试
```
- 数据库 `redgum.db` 首次启动自动建表并写入种子;删除文件即重置;
- 演示账号:`deb` / `helen` / `tomas`,密码 `redgum123`;
- 开发环境(本机):`uv venv --python 3.12 && uv pip install -r requirements.txt`,再 `uv run uvicorn ...` / `uv run pytest`。

---

## 12. Git 流程

- 新仓库(本地 `~/redgum-tutoring`,远端待用户创建后推送);
- 每故事一分支:`story/01-foundation` → … → `story/10-delivery`;
- 合并策略与上个项目一致:按顺序 `--no-ff` 合并到 `main`,保留"每故事一分支"的痕迹;
- 提交规范:`feat(story-NN): …` / `fix(story-NN): …` / `test(story-NN): …` / `docs(story-NN): …`。

---

## 13. 假设与决策(同步到 Confluence)

1. 可用时段按"星期几"存储,学期制;卡片上的中途修改通过编辑该窗口体现(不做历史版本)。
2. 时长仅 60/90 分钟(案例明确);其他时长拒绝。
3. 中心仅周二–周六运营,可用时段的星期选择仅提供这五天。
4. 已取消/已出席/已缺席为终态,不可再改期(案例未要求恢复;如需恢复属 backlog)。
5. 改期仅允许改日期、开始时间、时长(学生/导师/科目不变),且重新校验可用时段。
6. 过去日期的排课不拦截(案例无此规则;日记本本身就是历史记录)。
7. 导师停用后不出现在新排课下拉,但历史课时与其姓名照常显示。
8. 不做时区处理,时间按本地时间直接比较。
9. 列表用搜索/筛选代替分页(规模不需要)。
10. 页面与文案为英文(课程与验收语境);日期时间显示为 `Sat 15 Aug 2026, 9:00 am` 风格。
11. 冲突/重叠检测、房间分配明确不做(案例排除)。

---

## 14. 已知限制(写入交接文档)

1. 会话 cookie 无 CSRF token(SameSite=Lax 缓解);无登录限流与密码找回。
2. SQLite 单文件适合本规模与课程演示,不适合多实例部署。
3. 无并发写保护(同一课时并发修改后写覆盖)。
4. 无审计日志(谁改了什么)。
5. 无学期/假期日历:可用时段按星期几,不感知学期日期与"第 8 周不可用"。
6. 无课时提醒、无家长门户、无收费(案例排除)。
7. 前端无自动化测试;行为由 pytest 端到端覆盖。
8. 导师周课时上限(8 节)不校验(案例未要求,进 backlog)。
