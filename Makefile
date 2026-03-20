.PHONY: bump

bump: ## Bump the version numbers to $VERSION
ifeq ($(VERSION),)
	@$(error VERSION is not defined. Run with `make VERSION=number bump`)
endif
	@echo Bumping the version number to $(VERSION)
	@sed -i.bak "s/__version__ = '.*'/__version__ = '$(VERSION)'/" bugsnag/__init__.py && rm bugsnag/__init__.py.bak
	@sed -i.bak "s/version='.*',/version='$(VERSION)',/" setup.py && rm setup.py.bak
	@sed -i.bak "s/'version': '.*'/'version': '$(VERSION)'/" bugsnag/notifier.py && rm bugsnag/notifier.py.bak
	@echo "Successfully bumped version to $(VERSION)"
	@echo "Updated files: bugsnag/__init__.py, setup.py, bugsnag/notifier.py"
