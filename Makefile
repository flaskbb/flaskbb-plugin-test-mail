.PHONY: clean help test lint update-translations compile-translations add-translation dist upload

help:
	@echo "  clean                  remove unwanted stuff"
	@echo "  test                   run the testsuite"
	@echo "  lint                   check the source for style errors"
	@echo "  update-translations    updates the translations"
	@echo "  compile-translations   compiles the translations"
	@echo "  add-translation        adds a new language to the translations"
	@echo "  dist                   creates distribution packages"
	@echo "  upload                 uploads a new version of the wheel package to PyPI"

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

test:
	uv run pytest

lint:
	uv run ruff check

update-translations:
	pybabel extract -F babel.cfg -k lazy_gettext -o test_mail/translations/messages.pot .
	pybabel update -i test_mail/translations/messages.pot -d test_mail/translations/

add-translation:
	@read -p "Enter new language shortcode:" lang; \
	pybabel init -i test_mail/translations/messages.pot -d test_mail/translations/ -l $$lang

compile-translations:
	pybabel compile -d test_mail/translations/

dist:
	uv build

upload: dist
	uv publish
