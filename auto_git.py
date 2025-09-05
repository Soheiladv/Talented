import os
import subprocess
from pathlib import Path

# -----------------------------
# تنظیمات اولیه
# -----------------------------
project_root = Path(__file__).parent.resolve()
gitignore_path = project_root / ".gitignore"
version_file = project_root / "VERSION"
commit_message = "Auto-update .gitignore, clean repo and bump version"

# -----------------------------
# محتویات gitignore
# -----------------------------
gitignore_content = """
# ==== Gitignore for Talented Project ====

# Python
*.pyc
__pycache__/
.venv/
venv/
.env

# Logs and outputs
logs/
*.log
outputs/
*.txt

# Backups
backups/
*.sql
*.rar

# Django
*.sqlite3
staticfiles/
media/
mediafiles/
**/migrations/*.pyc
**/migrations/__pycache__/

# IDE and system
.vscode/
.idea/
.DS_Store
Thumbs.db

# Node
node_modules/
npm-debug.log
yarn-error.log

# Build
build/
dist/
*.egg-info/

# Model folders
bolbolzaban/
distilgpt2/
gpt-neo-125M/
phi-1_5/
"""

# -----------------------------
# ایجاد یا بروزرسانی .gitignore
# -----------------------------
with open(gitignore_path, "w", encoding="utf-8") as f:
    f.write(gitignore_content)
print("✅ .gitignore created/updated")

# -----------------------------
# حذف فایل‌های کش شده که نباید باشند
# -----------------------------
subprocess.run(["git", "rm", "-r", "--cached", "."], cwd=project_root)
print("✅ Removed cached files from Git")

# -----------------------------
# نسخه‌بندی خودکار Semantic Versioning
# -----------------------------
if version_file.exists():
    with open(version_file, "r") as f:
        version = f.read().strip()
else:
    version = "0.0.0"

# افزایش patch
major, minor, patch = map(int, version.split("."))
patch += 1
new_version = f"{major}.{minor}.{patch}"

with open(version_file, "w") as f:
    f.write(new_version)
print(f"✅ Version bumped: {version} -> {new_version}")

# -----------------------------
# اضافه کردن تغییرات و commit
# -----------------------------
subprocess.run(["git", "add", "."], cwd=project_root)
subprocess.run(["git", "commit", "-m", f"{commit_message} (v{new_version})"], cwd=project_root)
print("✅ Changes added and committed")

# -----------------------------
# ساخت tag جدید
# -----------------------------
subprocess.run(["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"], cwd=project_root)
print(f"✅ Tag created: v{new_version}")

# -----------------------------
# (اختیاری) push به remote
# -----------------------------
# subprocess.run(["git", "push"], cwd=project_root)
# subprocess.run(["git", "push", "--tags"], cwd=project_root)
# print("✅ Pushed commits and tags to remote")
