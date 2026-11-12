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
# Every uv call goes through the vendored helper, which cleans the environment,
# uses the global uv cache, runs offline first and goes online at most once. See
# https://github.com/leynos/shared-actions/tree/main/uv_gate for the contract.
UV_GATE ?= python3 scripts/uv_gate.py
UV ?= uv
# The helper finds uv on PATH, so a caller's UV=/path/to/uv is honoured by putting
# that uv's directory first on PATH for every recipe.
export PATH := $(if $(findstring /,$(UV)),$(patsubst %/,%,$(dir $(UV))):)$(PATH)
TOOLS = $(MDLINT)
VENV_TOOLS = pytest
# The CV-005 CodeScene contracts live in shared-actions and run from a full
# commit, so a fix is a pin bump. `.github/cv005.toml` holds this repository's
# only parameters.
CV005_CONTRACTS_REF ?= a38feb9be25755c30eca5bda96bd3786a5b89c6b
CV005_CONTRACTS = $(UV_GATE) tool --python 3.13 --from 'git+https://github.com/leynos/shared-actions@$(CV005_CONTRACTS_REF)\#subdirectory=packages/cv005-contracts' -- cv005-contracts
PYLINT_PYTHON ?= pypy@3.12
PYLINT_VERSION ?= 4.0.9
PYLINT_TARGETS ?= beatcue tests
PYLINT = $(UV_GATE) tool --managed-python --python $(PYLINT_PYTHON) --from 'pylint==$(PYLINT_VERSION)' -- pylint
# The dead-code gate is the installed df12-skylos command; its `skylos` extra
# carries the one Skylos pin. Skylos parses source with its own runtime AST, so
# the tool environment runs Python 3.14.
DF12_PYTHON_LINTS_SHA = 1d6c3bba594651823c9ba8e8b40265cae59a1c52
SKYLOS = $(UV_GATE) tool --python 3.14 --from \
  'df12-python-lints[skylos] @ git+https://github.com/leynos/df12-python-lints.git@$(DF12_PYTHON_LINTS_SHA)' \
  -- df12-skylos
TYPOS_VERSION ?= 1.48.0
TYPOS := $(UV_GATE) tool --from typos@$(TYPOS_VERSION) -- typos

.PHONY: prepare help all clean build build-release lint fmt check-fmt \
        check-architecture interrogate markdownlint nixie skylos skylos-allow spelling test \
        test-workflow-contracts typecheck $(TOOLS) $(VENV_TOOLS)

prepare: .deps ## Install the locked development environment, offline first

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

.deps: pyproject.toml uv.lock .venv
	$(call ensure_uv)
	$(UV_GATE) prepare --group dev
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
	@$(UV_GATE) run -- which $(1) >/dev/null 2>&1 || { \
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
$(VENV_TOOLS): prepare ## Verify required CLI tools in venv
	$(call ensure_tool_venv,$@)
endif

fmt: .deps ## Format sources
	$(call ensure_uv)
	$(UV_GATE) run -- ruff format
	$(UV_GATE) run -- ruff check --select I --fix
	$(MDTABLEFIX) --in-place $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)
	$(MDLINT) --fix "**/*.md"

check-fmt: .deps ## Verify formatting
	$(call ensure_uv)
	$(UV_GATE) run -- ruff format --check
	$(MDTABLEFIX) --check $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)

# Interrogate scans each target recursively, subject to its default exclusions.
# Add a new Python directory to the targets.
INTERROGATE_VERSION ?= 1.7.0
INTERROGATE_TARGETS ?= beatcue scripts tests
# Level 2 prints a MISSED row per undocumented definition, which the
# `interrogate` recipe below looks for: the rounded percentage alone can pass a
# lone gap.
INTERROGATE_FLAGS ?= -vv --fail-under 100
INTERROGATE ?= $(UV_GATE) tool --python 3.13 --from 'interrogate==$(INTERROGATE_VERSION)' -- interrogate

# Interrogate rounds its percentage to one decimal, so `--fail-under 100` alone
# can pass a lone gap in a large repository. This recipe also fails when `grep`
# finds a MISSED row in the report on standard output, which `-vv` or higher
# prints for each undocumented definition.
interrogate: ## Enforce complete Python docstring coverage
	@report="$$($(INTERROGATE) $(INTERROGATE_FLAGS) $(INTERROGATE_TARGETS))"; \
	  status=$$?; \
	  printf '%s\n' "$$report"; \
	  test "$$status" -eq 0 || exit "$$status"; \
	  if printf '%s\n' "$$report" | grep -q '| *MISSED *|'; then \
	    printf '%s\n' 'interrogate: undocumented definitions remain; see the MISSED rows above' >&2; \
	    exit 1; \
	  fi

lint: .deps ## Run linters
	$(call ensure_uv)
	$(MAKE) --no-print-directory interrogate
	$(UV_GATE) run -- ruff check
	$(PYLINT) $(PYLINT_TARGETS)
	$(MAKE) check-architecture
	+$(MAKE) spelling
	$(MAKE) --no-print-directory skylos

skylos: ## Detect dead production code
	$(SKYLOS) check --repository .

skylos-allow: ## Document one named Skylos exception (SYMBOL=name REASON=text)
	$(SKYLOS) allow --repository . --symbol '$(SYMBOL)' --reason '$(REASON)'

check-architecture: .deps ## Verify hexagonal import boundaries
	$(call ensure_uv)
	$(UV_GATE) run -- hecate check

typecheck: .deps ## Run typechecking
	$(call ensure_uv)
	$(UV_GATE) run -- ty --version
	# scripts/generate_typos_config.py imports its sibling helper by module
	# name and scripts/ is not a package, so the directory goes on the search
	# path. ty 0.0.78 accepts environment.extra-paths in pyproject.toml but
	# does not apply it to resolution; the flag does work.
	$(UV_GATE) run -- ty check --extra-search-path scripts

markdownlint: $(MDLINT) ## Lint Markdown files
	$(MDLINT) '**/*.md'
	+$(MAKE) spelling

spelling: prepare ## Enforce en-GB-oxendict spelling in Markdown prose
	@$(UV_GATE) run -- python scripts/generate_typos_config.py
	@find . -type f -name '*.md' -not -path './.venv/*' -print0 | \
		xargs -0 -r $(TYPOS) --config typos.toml --force-exclude

nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,nixie)
	$(NIXIE) --no-sandbox

test: .deps $(VENV_TOOLS) test-workflow-contracts ## Run tests
	$(call ensure_uv)
	$(UV_GATE) run -- pytest -v -n auto

test-workflow-contracts: ## Run the shared CV-005 CodeScene contracts
	$(call ensure_uv)
	$(CV005_CONTRACTS) check --repository .

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":"; printf "Available targets:\n"} {printf "  %-20s %s\n", $$1, $$2}'
