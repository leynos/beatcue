MDLINT ?= markdownlint-cli2
NIXIE ?= nixie
MDFORMAT_ALL ?= mdformat-all
UV ?= uv
TOOLS = $(MDFORMAT_ALL) ty $(MDLINT)
VENV_TOOLS = pytest
UV_ENV = UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools
PYLINT_PYTHON ?= pypy
PYLINT_TARGETS ?= beatcue tests
PYLINT_PYPY_SHIM_REF ?= 726d09f968b4d729ee4b29c71fc732e744854f3b
PYLINT_PYPY_SHIM = git+https://github.com/leynos/pylint-pypy-shim.git@$(PYLINT_PYPY_SHIM_REF)
PYLINT = $(UV_ENV) $(UV) tool run --python $(PYLINT_PYTHON) --from '$(PYLINT_PYPY_SHIM)' pylint-pypy

.PHONY: help all clean build build-release lint fmt check-fmt \
        check-architecture markdownlint nixie test typecheck $(TOOLS) \
        $(VENV_TOOLS)

.DEFAULT_GOAL := all

all: build check-fmt lint typecheck test

define ensure_uv
	@command -v "$(UV)" >/dev/null 2>&1 || { \
	  printf "Error: 'uv' is required, but not installed or not executable at '%s'\n" "$(UV)" >&2; \
	  exit 1; \
	}
endef

.venv: pyproject.toml
	$(call ensure_uv)
	$(UV_ENV) $(UV) venv --clear

.deps: pyproject.toml uv.lock .venv
	$(call ensure_uv)
	$(UV_ENV) $(UV) sync --group dev
	@touch $@

build: .deps ## Build virtual-env and install deps

build-release: ## Build artefacts (sdist & wheel)
	python -m build --sdist --wheel

clean: ## Remove build artifacts
	rm -rf build dist *.egg-info \
	  .mypy_cache .pytest_cache .coverage coverage.* \
	  lcov.info htmlcov .venv .deps
	find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required, but not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

define ensure_tool_venv
	$(call ensure_uv)
	@$(UV_ENV) $(UV) run which $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required in the virtualenv, but is not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

ifneq ($(strip $(TOOLS)),)
$(TOOLS): ## Verify required CLI tools
	$(call ensure_tool,$@)
endif


ifneq ($(strip $(VENV_TOOLS)),)
.PHONY: $(VENV_TOOLS)
$(VENV_TOOLS): ## Verify required CLI tools in venv
	$(call ensure_tool_venv,$@)
endif

fmt: .deps $(MDFORMAT_ALL) ## Format sources
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ruff format
	$(UV_ENV) $(UV) run ruff check --select I --fix
	$(MDFORMAT_ALL)

check-fmt: .deps ## Verify formatting
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ruff format --check
	# mdformat-all doesn't currently do checking

lint: .deps ## Run linters
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ruff check
	$(PYLINT) $(PYLINT_TARGETS)
	$(MAKE) check-architecture

check-architecture: .deps ## Verify hexagonal import boundaries
	$(call ensure_uv)
	$(UV_ENV) $(UV) run hecate check

typecheck: .deps ty ## Run typechecking
	ty --version
	ty check

markdownlint: $(MDLINT) ## Lint Markdown files
	$(MDLINT) '**/*.md'

nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,nixie)
	$(NIXIE) --no-sandbox

test: .deps $(VENV_TOOLS) ## Run tests
	$(call ensure_uv)
	$(UV_ENV) $(UV) run pytest -v -n auto

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":"; printf "Available targets:\n"} {printf "  %-20s %s\n", $$1, $$2}'
