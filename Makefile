PYTHON ?= python3
BACKEND_DIR = backend

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r $(BACKEND_DIR)/requirements.txt

run-backend:
	PYTHONPATH=$(BACKEND_DIR) . .venv/bin/activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test-backend:
	PYTHONPATH=$(BACKEND_DIR) . .venv/bin/activate && pytest $(BACKEND_DIR)/tests
