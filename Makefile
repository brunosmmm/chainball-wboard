
STATIC_PATH:=web_board/static
DIST_FILES:=$(STATIC_PATH)/dist/main.css $(STATIC_PATH)/dist/bundle.js
SOURCE_FILES:=$(STATIC_PATH)/js/index.js $(STATIC_PATH)/webpack.config.js $(STATIC_PATH)/package.json

all: $(DIST_FILES)

$(DIST_FILES): $(SOURCE_FILES)
	cd $(STATIC_PATH) && npm run build && ./update_bundle
