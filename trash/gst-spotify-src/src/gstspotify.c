#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include <gst/gst.h>

#include "gstspotifysrc.h"

static gboolean
spotify_init (GstPlugin * plugin)
{
  return gst_element_register (plugin, "spotify", GST_RANK_NONE,
      GST_TYPE_SPOTIFY);
}

GST_PLUGIN_DEFINE (GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    "spotify",
    "spotify plugin",
    spotify_init, VERSION, "LGPL", "dogvibes", "http://code.google.com/p/dogvibes/");
