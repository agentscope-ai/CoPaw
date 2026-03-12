# Skill多Workspace支持修复

## 问题描述

之前的skill相关API大多数还在使用全局的默认目录（`~/.copaw/active_skills`和`~/.copaw/customized_skills`），导致所有workspace共享同一套技能配置，而不是每个workspace独立管理。

## 修复内容

### 1. 重构 `SkillService` 类 (skills_manager.py)

**修改前**: 静态类，所有方法使用全局常量目录
```python
class SkillService:
    @staticmethod
    def create_skill(...) -> bool:
        customized_dir = get_customized_skills_dir()  # 全局目录
        ...
```

**修改后**: 实例类，每个实例绑定到特定workspace
```python
class SkillService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def create_skill(self, ...) -> bool:
        customized_dir = get_customized_skills_dir(self.workspace_dir)
        ...
```

**修改的方法**:
- `list_all_skills()` → 实例方法
- `list_available_skills()` → 实例方法
- `create_skill()` → 实例方法
- `disable_skill()` → 实例方法
- `enable_skill()` → 实例方法
- `delete_skill()` → 实例方法
- `sync_from_active_to_customized()` → 实例方法
- `load_skill_file()` → 实例方法

**修改的辅助函数**:
- `get_customized_skills_dir(workspace_dir)` - 新增workspace_dir参数
- `get_active_skills_dir(workspace_dir)` - 新增workspace_dir参数
- `get_working_skills_dir(workspace_dir)` - 新增workspace_dir参数
- `sync_skills_to_working_dir(workspace_dir, ...)` - 新增workspace_dir参数
- `sync_skills_from_active_to_customized(workspace_dir, ...)` - 新增workspace_dir参数
- `list_available_skills(workspace_dir)` - 新增workspace_dir参数
- `ensure_skills_initialized(workspace_dir)` - 新增workspace_dir参数

### 2. 更新 skills_hub.py

**修改**:
- `install_skill_from_hub()` 新增 `workspace_dir: Path` 参数
- 在函数内创建 `SkillService` 实例：`skill_service = SkillService(workspace_dir)`

### 3. 更新 API路由 (app/routers/skills.py)

修改以下API端点，使其从request获取workspace并创建workspace绑定的SkillService：

- ✅ `GET /skills` - **改用SkillService.list_all_skills()** (原来手动遍历目录)
- ✅ `GET /skills/available` - **改用SkillService.list_available_skills()** (原来手动遍历目录)
- ✅ `POST /skills/batch-disable` - 现在使用workspace绑定的skill_service
- ✅ `POST /skills/batch-enable` - 现在使用workspace绑定的skill_service
- ✅ `POST /skills` (create_skill) - 现在使用workspace绑定的skill_service
- ✅ `DELETE /skills/{skill_name}` - 现在使用workspace绑定的skill_service
- ✅ `POST /skills/hub/install` - 传入workspace_dir参数
- ✅ `GET /skills/{skill_name}/files/{source}/{file_path}` - 现在使用workspace绑定的skill_service

**已支持多workspace的API** (无需修改):
- `POST /skills/{skill_name}/enable` - 已经使用workspace目录
- `POST /skills/{skill_name}/disable` - 已经使用workspace目录
- `GET /skills/hub/search` - 不依赖workspace

### 4. 更新 react_agent.py

**修改**:
- `_register_skills()` 方法现在使用 `self._workspace_dir` 而不是全局目录
- 调用 `ensure_skills_initialized(workspace_dir)`
- 调用 `get_working_skills_dir(workspace_dir)`
- 调用 `list_available_skills(workspace_dir)`

### 5. 更新 CLI命令

对于CLI命令（非多workspace环境），使用默认的WORKING_DIR：

**skills_cmd.py**:
- `configure_skills_interactive()` - 创建 `SkillService(WORKING_DIR)` 实例
- `list_cmd()` - 使用 `SkillService(WORKING_DIR)`

**init_cmd.py**:
- `sync_skills_to_working_dir()` 调用时传入 `workspace_dir=WORKING_DIR`

## 技术细节

### Workspace隔离

每个workspace现在有独立的技能目录结构：
```
{workspace_dir}/
├── active_skills/       # 已启用的技能
│   └── skill_name/
│       ├── SKILL.md
│       ├── references/
│       └── scripts/
└── customized_skills/   # 用户自定义的技能
    └── skill_name/
        ├── SKILL.md
        ├── references/
        └── scripts/
```

### Builtin技能

Builtin技能仍然是全局共享的（位于代码目录中），但每个workspace可以独立决定是否启用它们。

## 测试

创建了测试验证workspace隔离功能：
```bash
pytest test_skill_multi_workspace.py -v
```

测试验证了：
- 在workspace1创建的技能不会出现在workspace2
- 在workspace1启用的技能不会影响workspace2
- 每个workspace独立管理自己的技能列表

## 向后兼容

- CLI命令仍然使用默认的 `~/.copaw/` 目录
- 所有API路由自动从request获取workspace，无需前端修改
- 旧的单workspace代码迁移到多workspace环境无需修改

## 补充修复：统一使用SkillService

在code review中发现 `GET /skills` 和 `GET /skills/available` 这两个API端点没有使用 `SkillService`，而是手动遍历目录。已修复为统一使用 `SkillService`：

**修改前**:
```python
# 手动遍历builtin、customized、active目录
for skill_dir in builtin_skills_dir.iterdir():
    if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
        # 手动读取文件...
```

**修改后**:
```python
# 使用SkillService统一管理
skill_service = SkillService(workspace_dir)
all_skills = skill_service.list_all_skills()  # 或 list_available_skills()
# 转换为API响应格式
```

**优势**:
- ✅ 代码重用，减少重复逻辑
- ✅ 统一的目录访问方式
- ✅ 更容易维护和测试
- ✅ 保证所有API端点行为一致

## Pre-commit检查

所有修改的文件都通过了pre-commit检查：
- ✓ mypy类型检查
- ✓ black代码格式化
- ✓ flake8代码质量检查
- ✓ pylint代码质量检查
