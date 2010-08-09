#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include <gst/gst.h>

#include "gstspotsrc.h"

static gboolean
spot_init (GstPlugin * plugin)
{
  return gst_element_register (plugin, "spot", GST_RANK_NONE,
      GST_TYPE_SPOT_SRC);
}

GST_PLUGIN_DEFINE (GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    "spot",
    "spot plugin",
    spot_init, VERSION, "LGPL", "dogvibes", "http://code.google.com/p/dogvibes/");
