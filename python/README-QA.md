# Workshop Q&A (Python Edition): Windows Setup Fixes for New Machines

This guide captures the exact setup and troubleshooting steps validated while testing on a fresh Windows machine. Run every command below from the `python` folder of the repository.

For the Spring + LangChain4j edition, see [../spring/README-QA.md](../spring/README-QA.md).

## Q1) I get long package install errors while running pip install

### Symptom

You may see an error similar to:

- Could not install packages due to an OSError: [Errno 2] No such file or directory
- HINT: This error might have occurred since this system does not have Windows Long Path support enabled
- The failing path often includes Streamlit files under a long AppData location

### Why this happens

Installing globally can use a very long path under AppData, which may hit Windows path-length limits.

### Fix (recommended)

Install everything inside a project-local virtual environment so paths are shorter.

```powershell
Set-Location C:\Users\<USER_NAME>\Dev\Flo_workshop_2026\python

# 1) Create local virtual environment
python -m venv .venv

# 2) Activate it (PowerShell)
.\.venv\Scripts\Activate.ps1

# 3) Upgrade pip
python -m pip install --upgrade pip

# 4) Install workshop dependencies
python -m pip install -r requirements.txt
```

If your machine has multiple Python versions and python is not recognized, try:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Q2) Activate.ps1 failed or returned exit code 1

### Symptom

PowerShell fails when running:

- .\\.venv\\Scripts\\Activate.ps1

### Why this happens

PowerShell execution policy may block local scripts.

### Fix

Use a process-only bypass (safe for current terminal session only), then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternative if policy is managed by your organization: skip activation and call the venv Python directly:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

## Q3) Warnings say script .exe is not on PATH

### Symptom

Warnings like:

- The script websockets.exe is installed in ... Scripts which is not on PATH

### Is this a blocker?

No. These are warnings, not installation failures.

### Fix/Best practice

Inside the virtual environment, prefer module execution:

```powershell
python -m streamlit run app.py
```

If not activated:

```powershell
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

## Q4) pytest command fails (No module named pytest)

### Symptom

Test command fails with:

- No module named pytest

### Fix

Install pytest in the virtual environment and rerun:

```powershell
python -m pip install pytest
python -m pytest -q
```

If not activated:

```powershell
& .\.venv\Scripts\python.exe -m pip install pytest
& .\.venv\Scripts\python.exe -m pytest -q
```

## Q5) .\\.venv\\Scripts\\python.exe not recognized in PowerShell

### Symptom

PowerShell may throw CommandNotFoundException for the direct path.

### Fix

Use the call operator (&):

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m streamlit --version
```

## Verified end-to-end setup commands (copy/paste)

Use this full sequence on a new machine:

```powershell
Set-Location C:\Users\<USER_NAME>\Dev\Flo_workshop_2026\python
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit --version
python -m streamlit run app.py
```

## Optional system-level improvement

If your team prefers global installs, you can enable Windows Long Paths system-wide. However, for workshop reliability, the project-local .venv approach above is the recommended default.
