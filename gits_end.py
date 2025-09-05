import os
import subprocess

# -----------------------------
# تنظیمات اولیه
# -----------------------------
project_root = os.path.dirname(os.path.abspath(__file__))
gitignore_path = os.path.join(project_root, ".gitignore")
commit_message = "Auto-update .gitignore and clean repo"

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
# اضافه کردن تغییرات و commit
# -----------------------------
subprocess.run(["git", "add", "."], cwd=project_root)
subprocess.run(["git", "commit", "-m", commit_message], cwd=project_root)
print("✅ Changes added and committed")

# -----------------------------
# (اختیاری) push به remote
# -----------------------------
# subprocess.run(["git", "push"], cwd=project_root)
# print("✅ Pushed to remote")


from datetime import datetime
version = datetime.now().strftime("v%Y.%m.%d-%H%M")
subprocess.run(["git", "tag", "-a", version, "-m", f"Auto tag {version}"])
subprocess.run(["git", "push", "--tags"])
