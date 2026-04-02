SHELL := /bin/bash
VENV := .venv

HOST ?= 127.0.0.1
PORT ?= 8001

PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

.PHONY: setup install dev run clean

setup:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating venv ($(VENV))..."; \
		python3 -m venv "$(VENV)"; \
	fi
	$(MAKE) install

install:
	@echo "Installing requirements..."
	$(PIP) install -r requirements.txt

# Development server (with autoreload)
dev: setup
	@echo "Starting dev server at http://$(HOST):$(PORT)/"
	$(UVICORN) app.main:app --reload --host $(HOST) --port $(PORT)

# Production-like run (no autoreload)
run: setup
	@echo "Starting server at http://$(HOST):$(PORT)/"
	$(UVICORN) app.main:app --host $(HOST) --port $(PORT)

clean:
	@echo "Removing venv ($(VENV))..."
	rm -rf "$(VENV)"
