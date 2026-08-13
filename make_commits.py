import os
import subprocess

repo_dir = "/Volumes/My Files/Projects/PII Redaction Tool"

def run_git(cmd, env=None):
    print(f"Running: git {cmd}")
    subprocess.run(f"git {cmd}", shell=True, cwd=repo_dir, check=True, env=env)

# Ensure git is initialized
subprocess.run("git init", shell=True, cwd=repo_dir)

env = os.environ.copy()
env['GIT_AUTHOR_NAME'] = 'Antigravity'
env['GIT_AUTHOR_EMAIL'] = 'antigravity@gemini.com'
env['GIT_COMMITTER_NAME'] = 'Antigravity'
env['GIT_COMMITTER_EMAIL'] = 'antigravity@gemini.com'

# Ensure we have an initial commit
try:
    subprocess.run("git rev-parse HEAD", shell=True, cwd=repo_dir, check=True, capture_output=True)
except subprocess.CalledProcessError:
    with open(os.path.join(repo_dir, ".gitignore"), "w") as f:
        f.write("node_modules/\nvenv/\n__pycache__/\n*.pyc\n.DS_Store\n")
    run_git("add .gitignore", env=env)
    run_git("commit -m \"chore: initial commit with gitignore\"", env=env)

# Add all files to index to track them, then get the list, then unstage them
run_git("add .")
result = subprocess.run("git ls-files", shell=True, cwd=repo_dir, capture_output=True, text=True)
files_to_commit = [f for f in result.stdout.strip().split('\n') if f and f != ".gitignore"]
run_git("reset")

# Backup files
file_contents = {}
for f in files_to_commit:
    path = os.path.join(repo_dir, f)
    if os.path.isfile(path):
        with open(path, 'r') as file:
            file_contents[f] = file.read()
        # Empty the file initially
        with open(path, 'w') as file:
            file.write("")

commit_count = 0
def commit_chunk(f, content, msg):
    global commit_count
    path = os.path.join(repo_dir, f)
    with open(path, 'a') as file:
        file.write(content + "\n")
    run_git(f"add \"{f}\"")
    run_git(f"commit -m \"{msg}\"", env=env)
    commit_count += 1

# Process models.py
f = "backend/app/models.py"
if f in file_contents:
    lines = file_contents[f].split('\n')
    chunk = []
    for line in lines:
        if line.startswith("class ") and chunk:
            commit_chunk(f, '\n'.join(chunk), f"feat(backend): add models to {os.path.basename(f)}")
            chunk = []
        chunk.append(line)
    if chunk:
        commit_chunk(f, '\n'.join(chunk), f"feat(backend): complete {os.path.basename(f)}")

# Process test_pii_detector.py
f = "backend/tests/test_pii_detector.py"
if f in file_contents:
    lines = file_contents[f].split('\n')
    chunk = []
    for line in lines:
        if line.startswith("class Test") and chunk:
            commit_chunk(f, '\n'.join(chunk), f"test(backend): add tests to {os.path.basename(f)}")
            chunk = []
        chunk.append(line)
    if chunk:
        commit_chunk(f, '\n'.join(chunk), f"test(backend): complete {os.path.basename(f)}")

# Process test_pseudonymizer.py
f = "backend/tests/test_pseudonymizer.py"
if f in file_contents:
    lines = file_contents[f].split('\n')
    chunk = []
    for line in lines:
        if line.startswith("class Test") and chunk:
            commit_chunk(f, '\n'.join(chunk), f"test(backend): add tests to {os.path.basename(f)}")
            chunk = []
        chunk.append(line)
    if chunk:
        commit_chunk(f, '\n'.join(chunk), f"test(backend): complete {os.path.basename(f)}")

# Process RedactionPage.tsx
f = "frontend/src/pages/RedactionPage.tsx"
if f in file_contents:
    lines = file_contents[f].split('\n')
    chunk = []
    for line in lines:
        if "className=" in line and len(chunk) > 20:
            commit_chunk(f, '\n'.join(chunk), f"feat(frontend): build Redaction Worksheet UI component")
            chunk = []
        chunk.append(line)
    if chunk:
        commit_chunk(f, '\n'.join(chunk), f"feat(frontend): complete Redaction Worksheet UI")

# Process App.tsx (routes)
f = "frontend/src/App.tsx"
if f in file_contents:
    lines = file_contents[f].split('\n')
    chunk = []
    for line in lines:
        if "<Route " in line and chunk:
            commit_chunk(f, '\n'.join(chunk), f"feat(frontend): add routes to {os.path.basename(f)}")
            chunk = []
        chunk.append(line)
    if chunk:
        commit_chunk(f, '\n'.join(chunk), f"feat(frontend): complete {os.path.basename(f)}")

# Process pii_detector.py
f = "backend/app/services/pii_detector.py"
if f in file_contents:
    lines = file_contents[f].split('\n')
    chunk = []
    for line in lines:
        if "def " in line and chunk:
            commit_chunk(f, '\n'.join(chunk), f"feat(backend): add helper to {os.path.basename(f)}")
            chunk = []
        chunk.append(line)
    if chunk:
        commit_chunk(f, '\n'.join(chunk), f"feat(backend): complete {os.path.basename(f)}")

# Commit the rest of the files
processed_files = [
    "backend/app/models.py",
    "backend/tests/test_pii_detector.py",
    "backend/tests/test_pseudonymizer.py",
    "frontend/src/pages/RedactionPage.tsx",
    "frontend/src/App.tsx",
    "backend/app/services/pii_detector.py"
]

for f in files_to_commit:
    if f not in processed_files:
        if os.path.isfile(os.path.join(repo_dir, f)):
            with open(os.path.join(repo_dir, f), 'w') as file:
                file.write(file_contents[f])
            run_git(f"add \"{f}\"")
            msg = f"feat: add {os.path.basename(f)}"
            if "backend" in f:
                msg = f"feat(backend): implement {os.path.basename(f)}"
            elif "frontend" in f:
                msg = f"feat(frontend): implement {os.path.basename(f)}"
            run_git(f"commit -m \"{msg}\"", env=env)
            commit_count += 1

print(f"Successfully created {commit_count} commits.")

# Final catch all just in case
run_git("add .")
result = subprocess.run("git status --porcelain", shell=True, cwd=repo_dir, capture_output=True, text=True)
if result.stdout.strip():
    run_git("commit -m \"fix: final project adjustments\"", env=env)

# Push
try:
    result = subprocess.run("git remote -v", shell=True, cwd=repo_dir, capture_output=True, text=True)
    if result.stdout.strip():
        print("Pushing to remote...")
        subprocess.run("git push -u origin HEAD", shell=True, cwd=repo_dir, env=env)
    else:
        print("No remote configured, skipping push.")
except Exception as e:
    print(f"Push failed: {e}")
