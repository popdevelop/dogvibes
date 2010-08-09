LDADD = $(prefix)/lib/libgstcheck-@GST_MAJORMINOR@.la \
        $(GST_OBJ_LIBS) \
        $(CHECK_LIBS)

REGISTRY_ENVIRONMENT = \
                       GST_REGISTRY=$(CHECK_REGISTRY)

TESTS_ENVIRONMENT = \
        $(REGISTRY_ENVIRONMENT)                                 \
        GST_PLUGIN_SYSTEM_PATH=                                 \
        GST_PLUGIN_PATH=$(top_builddir)/src:$(GSTPB_PLUGINS_DIR):$(GST_PLUGINS_DIR)

clean-local: clean-local-check

REGISTRY_CHECKS = \
	elements/spotsrc

check_PROGRAMS = $(REGISTRY_CHECKS)

TESTS = $(check_PROGRAMS)

VALGRIND_TESTS_DISABLE =

SUPPRESSIONS = $(top_srcdir)/common/gst.supp

elements_spotsrc_CFLAGS = $(GST_PLUGINS_BASE_CFLAGS) $(GST_CFLAGS)

elements_spotsrc_LDADD = \
	-lspotify \
        $(prefix)/lib/libgstbase-@GST_MAJORMINOR@.la \
        $(LDADD)
