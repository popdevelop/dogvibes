# plugindir is set in configure

##############################################################################
# change libgstplugin.la to something more suitable, e.g. libmysomething.la  #
##############################################################################
plugin_LTLIBRARIES = libgstspotify.la

##############################################################################
# for the next set of variables, rename the prefix if you renamed the .la,   #
#  e.g. libgstplugin_la_SOURCES => libmysomething_la_SOURCES                 #
#       libgstplugin_la_CFLAGS  => libmysomething_la_CFLAGS                  #
#       libgstplugin_la_LIBADD  => libmysomething_la_LIBADD                  #
#       libgstplugin_la_LDFLAGS => libmysomething_la_LDFLAGS                 #
##############################################################################

# sources used to compile this plug-in
libgstspotify_la_SOURCES = gstspotify.c gstspotifysrc.c

# flags used to compile this plugin
# add other _CFLAGS and _LIBS as needed

# FIXME why is not gstaudio included in files

libgstspotify_la_CFLAGS = $(GST_PLUGINS_BASE_CFLAGS) $(GST_BASE_CFLAGS) $(GST_CFLAGS) \
	-I$(prefix)/include
libgstspotify_la_LIBADD = $(GST_LIBS) $(prefix)/lib/libgstaudio-0.10.la
libgstspotify_la_LDFLAGS = $(GST_PLUGIN_LDFLAGS) -lspotify
libgstspotify_la_LIBTOOLFLAGS = --tag=disable-static

# headers we need but don't want installed
noinst_HEADERS = gstspotifysrc.h
