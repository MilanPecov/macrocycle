.PHONY: install test release release-patch release-minor release-major

install:
	pip install -e .[dev]

test:
	pytest

# Bump version, update changelog, commit, tag, and push
release:
	cz bump --yes
	git push origin main --tags

release-patch:
	cz bump --increment PATCH --yes
	git push origin main --tags

release-minor:
	cz bump --increment MINOR --yes
	git push origin main --tags

release-major:
	cz bump --increment MAJOR --yes
	git push origin main --tags
