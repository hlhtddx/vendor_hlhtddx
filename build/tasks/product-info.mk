# Print a list of the modules that could be built
PRODUCT_INFO_JSON := $(PRODUCT_OUT)/product-info.json
VENDOR_TOOL_PATH := $(call my-dir)/../tools

product := $(INTERNAL_PRODUCT)

$(PRODUCT_INFO_JSON):
	@echo Generating $@
	$(hide) echo -ne '{ \n' > $@
	$(hide) echo -ne ' "name": "$(product)", \n' >> $@
	$(hide) echo -ne ' "model": "$(PRODUCTS.$(product).PRODUCT_MODEL))", \n' >> $@
	$(hide) echo -ne ' "device": "$(PRODUCTS.$(product).PRODUCT_DEVICE))", \n' >> $@
	$(hide) echo -ne ' "host_out": "$(HOST_OUT)", \n' >> $@
	$(hide) echo -ne ' "product_out": "$(PRODUCT_OUT)", \n' >> $@
	$(hide) echo -ne ' "packages": [$(foreach w,$(sort $(PRODUCTS.$(product).PRODUCT_PACKAGES)),"$(w)", )], \n' | sed -e 's/, *\]/]/g' -e 's/, *\}/ }/g' -e '$$s/,$$//' >> $@
	$(hide) echo -ne ' "copy-files": [$(foreach w,$(sort $(PRODUCTS.$(product).PRODUCT_COPY_FILES)),"$(w)", )], \n' | sed -e 's/, *\]/]/g' -e 's/, *\}/ }/g' -e '$$s/,$$//' >> $@
	$(hide) echo -ne ' "boot-jars": [$(foreach w,$(sort $(PRODUCTS.$(product).PRODUCT_BOOT_JARS)),"$(w)", )] \n' | sed -e 's/, *\]/]/g' -e 's/, *\}/ }/g' -e '$$s/,$$//' >> $@
	$(hide) echo -ne '}\n' >> $@

.PHONY: product-module-dot
.PHONY: my_dbg_files

product-module-dot: $(PRODUCT_INFO_JSON) $(MODULE_INFO_JSON) $(MODULE_DEPS_JSON)
	@echo Generating $@
	$(hide) python ${VENDOR_TOOL_PATH}/product_deps_graph.py
	$(hide) python ${VENDOR_TOOL_PATH}/product_deps_graph.py -t exe
	$(hide) python ${VENDOR_TOOL_PATH}/product_deps_graph.py -t apk
	$(hide) python ${VENDOR_TOOL_PATH}/product_deps_graph.py -t etc

$(PRODUCT_OUT)/module-apk.dot: product-module-dot
$(PRODUCT_OUT)/module-apk.svg: $(PRODUCT_OUT)/module-apk.dot
	@echo Generating $@
	$(hide) dot -Tsvg -Nshape=box -o $@ $<
my_dbg_files: $(PRODUCT_OUT)/module-apk.svg

$(PRODUCT_OUT)/module-exe.dot: product-module-dot
$(PRODUCT_OUT)/module-exe.svg: $(PRODUCT_OUT)/module-exe.dot
	@echo Generating $@
	$(hide) dot -Tsvg -Nshape=box -o $@ $<
my_dbg_files: $(PRODUCT_OUT)/module-exe.svg

define generate_product_module_graph
$(error, my_dbg_files depends on $(PRODUCT_OUT)/product-$(1).svg)
$(PRODUCT_OUT)/product-$(1).dot: product-module-dot
$(PRODUCT_OUT)/product-$(1).svg: $(PRODUCT_OUT)/product-$(1).dot
	@echo Generating $@
	$(hide) dot -Tsvg -Nshape=box -o $@ $<
my_dbg_files: $(PRODUCT_OUT)/product-$(1).svg
endef

$(foreach m,apk exe etc,$(call generate_product_module_graph($m)))

# If ONE_SHOT_MAKEFILE is set, our view of the world is smaller, so don't
# rewrite the file in that came.
ifndef ONE_SHOT_MAKEFILE
files: $(PRODUCT_INFO_JSON)
endif
