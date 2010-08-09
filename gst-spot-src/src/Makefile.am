# plugindir is set in configure

##############################################################################
# change libgstplugin.la to something more suitable, e.g. libmysomething.la  #
##############################################################################
plugin_LTLIBRARIES = libgstspot.la

##############################################################################
# for the next set of variables, rename the prefix if you renamed the .la,   #
#  e.g. libgstplugin_la_SOURCES => libmysomething_la_SOURCES                 #
#       libgstplugin_la_CFLAGS  => libmysomething_la_CFLAGS                  #
#       libgstplugin_la_LIBADD  => libmysomething_la_LIBADD                  #
#       libgstplugin_la_LDFLAGS => libmysomething_la_LDFLAGS                 #
##############################################################################

# sources used to compile this plug-in
libgstspot_la_SOURCES = gstspot.c gstspotsrc.c

# flags used to compile this plugin
# add other _CFLAGS and _LIBS as needed

# FIXME why is not gstaudio included in files

libgstspot_la_CFLAGS = $(GST_PLUGINS_BASE_CFLAGS) $(GST_BASE_CFLAGS) $(GST_CFLAGS) \
	-I$(prefix)/include

libgstspot_la_LIBADD = $(GST_BASE_LIBS) $(GST_LIBS)
libgstspot_la_LDFLAGS = $(GST_PLUGIN_LDFLAGS) -lspotify
#libgstspot_la_LDFLAGS = $(GST_PLUGIN_LDFLAGS) -lopenspotify

libgstspot_la_LIBTOOLFLAGS = --tag=disable-static

# headers we need but don't want installed
noinst_HEADERS = gstspotsrc.h
