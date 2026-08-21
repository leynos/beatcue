MDLINT ?= markdownlint-cli2
# `make fmt` and `make check-fmt` call mdtablefix directly. `--git` selects the
# Markdown files Git tracks and `--include-untracked` adds the untracked files
# Git does not ignore, so a new document is formatted before it is staged.
# Both modes need mdtablefix 0.6.0 or later; CI pins the version at the
# install-mdtablefix step.
MDTABLEFIX ?= mdtablefix
MDTABLEFIX_SELECT = --git --include-untracked
MDTABLEFIX_RULES = --wrap --renumber --breaks --ellipsis --fences
NIXIE ?= nixie
UV ?= uv
TOOLS = $(MDLINT)
VENV_TOOLS = pytest
UV_ENV = UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools
# The CV-005 CodeScene contracts live in shared-actions and run from a full
# commit, so a fix is a pin bump. `.github/cv005.toml` holds this repository's
# only parameters.
CV005_CONTRACTS_REF ?= a38feb9be25755c30eca5bda96bd3786a5b89c6b
CV005_CONTRACTS = $(UV_ENV) $(UV) tool run --python 3.13 \
	--from 'git+https://github.com/leynos/shared-actions@$(CV005_CONTRACTS_REF)\#subdirectory=packages/cv005-contracts' \
	cv005-contracts
PYLINT_PYTHON ?= pypy@3.12
PYLINT_VERSION ?= 4.0.9
PYLINT_TARGETS ?= beatcue tests
PYLINT = $(UV_ENV) $(UV) tool run --managed-python --python $(PYLINT_PYTHON) --from 'pylint==$(PYLINT_VERSION)' pylint
SKYLOS_VERSION = 4.33.2
SKYLOS = $(UV_ENV) $(UV) tool run --from 'skylos==$(SKYLOS_VERSION)' skylos \
	--config-file pyproject.toml
SKYLOS_PRODUCTION_TARGETS ?= beatcue
TYPOS_VERSION ?= 1.48.0
TYPOS := $(UV) tool run typos@$(TYPOS_VERSION)

.PHONY: help all clean build build-release lint fmt check-fmt \
        check-architecture markdownlint nixie skylos-allow spelling test \
        test-workflow-contracts typecheck $(TOOLS) $(VENV_TOOLS)

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
	rm -f .typos-oxendict-base.json .typos-oxendict-base.toml
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

fmt: .deps ## Format sources
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ruff format
	$(UV_ENV) $(UV) run ruff check --select I --fix
	$(MDTABLEFIX) --in-place $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)
	$(MDLINT) --fix "**/*.md"

check-fmt: .deps ## Verify formatting
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ruff format --check
	$(MDTABLEFIX) --check $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)

lint: .deps ## Run linters
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ruff check
	$(PYLINT) $(PYLINT_TARGETS)
	$(MAKE) check-architecture
	+$(MAKE) spelling
	$(SKYLOS) $(SKYLOS_PRODUCTION_TARGETS) --category dead_code --gate --format concise --no-upload --no-provenance --no-grep-verify

skylos-allow: export SKYLOS_NAME = $(value NAME)
skylos-allow: export SKYLOS_REASON = $(value REASON)
skylos-allow: ## Document one named Skylos exception, not an entry point
	@test -n "$${SKYLOS_NAME}" || { printf "Error: NAME is required for a named whitelist exception\\n" >&2; exit 2; }
	@test -n "$${SKYLOS_REASON}" || { printf "Error: REASON is required for a named whitelist exception\\n" >&2; exit 2; }
	$(SKYLOS) whitelist "$${SKYLOS_NAME}" --reason "$${SKYLOS_REASON}"

check-architecture: .deps ## Verify hexagonal import boundaries
	$(call ensure_uv)
	$(UV_ENV) $(UV) run hecate check

typecheck: .deps ## Run typechecking
	$(call ensure_uv)
	$(UV_ENV) $(UV) run ty --version
	# scripts/generate_typos_config.py imports its sibling helper by module
	# name and scripts/ is not a package, so the directory goes on the search
	# path. ty 0.0.78 accepts environment.extra-paths in pyproject.toml but
	# does not apply it to resolution; the flag does work.
	$(UV_ENV) $(UV) run ty check --extra-search-path scripts

markdownlint: $(MDLINT) ## Lint Markdown files
	$(MDLINT) '**/*.md'
	+$(MAKE) spelling

spelling: ## Enforce en-GB-oxendict spelling in Markdown prose
	@$(UV) run scripts/generate_typos_config.py
	@find . -type f -name '*.md' -not -path './.venv/*' -print0 | \
		xargs -0 -r $(TYPOS) --config typos.toml --force-exclude

nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,nixie)
	$(NIXIE) --no-sandbox

test: .deps $(VENV_TOOLS) test-workflow-contracts ## Run tests
	$(call ensure_uv)
	$(UV_ENV) $(UV) run pytest -v -n auto

test-workflow-contracts: ## Run the shared CV-005 CodeScene contracts
	$(call ensure_uv)
	$(CV005_CONTRACTS) check --repository .

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":"; printf "Available targets:\n"} {printf "  %-20s %s\n", $$1, $$2}'
