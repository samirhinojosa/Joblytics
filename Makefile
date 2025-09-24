# Project settings
APP_NAME=joblytics
APP_MODULE=app.main:app
POETRY=poetry

# Install dependencies
install:
	@$(POETRY) install

# Clean Python cache files
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} + && \
	find . -type f -name '*.pyc' -delete

# Run Jupyter Lab
jupyter-lab:
	@$(POETRY) run jupyter lab

# Display help
help:
	@echo "Makefile commands:"
	@echo "  make install       	- Install dependencies via Poetry"
	@echo "  make clean         	- Remove __pycache__ and .pyc files"
	@echo "  make jupyter-lab       - Run Jupyter Lab"