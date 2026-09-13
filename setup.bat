python -m venv venv

venv\Scripts\python.exe -m pip install --upgrade pip

venv\Scripts\python.exe -m pip install av --only-binary=av

venv\Scripts\python.exe -m pip install -r requirements.txt

venv\Scripts\python.exe -m unittest test_refactor_clean.py