# --- Global build timestamp ---
export BUILD_DATE := $(shell python -c "import datetime; print(datetime.datetime.now(datetime.UTC).isoformat())")

PYPROJECT = pyproject.toml
BACKUP = pyproject.toml.bak

# Helper macro for building a single package
define build_one
	cp $(PYPROJECT) $(BACKUP)
	poetry run python tools/set_package.py $(1)
	poetry build
	make restore
endef

.PHONY: restore
restore:
	@if exist $(BACKUP) move /Y $(BACKUP) $(PYPROJECT)

# --- Build ALL packages (original project name, full wheel) ---
.PHONY: build-all
build-all:
	$(call build_one,all)

# --- Build individual utilities (renamed wheels) ---
.PHONY: build-save-email-attachments
build-save-email-attachments:
	$(call build_one,save_email_attachments)

.PHONY: build-crosshair-overlay
build-crosshair-overlay:
	$(call build_one,crosshair_overlay)

.PHONY: build-bulk-photo-processor
build-bulk-photo-processor:
	$(call build_one,bulk_photo_processor)

.PHONY: build-whatsapp-toolkit
build-whatsapp-toolkit:
	$(call build_one,WhatsApp_toolkit)