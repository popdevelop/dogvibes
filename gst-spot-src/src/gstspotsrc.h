/* GStreamer
 * Copyright (C) 2009 Joel Larsson
 *                    Johan Gyllenspetz
 *
 *
 * gstspotesrc.h:
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef __GST_SPOT_SRC_H__
#define __GST_SPOT_SRC_H__

#include <sys/types.h>

#include <gst/gst.h>
#include <libspotify/api.h>
#include <gst/base/gstadapter.h>
#include <gst/base/gstbasesrc.h>

G_BEGIN_DECLS

#define GST_TYPE_SPOT_SRC \
  (gst_spot_src_get_type ())
#define GST_SPOT_SRC(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj),GST_TYPE_SPOT_SRC,GstSpotSrc))
#define GST_SPOT_SRC_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass),GST_TYPE_SPOT_SRC,GstSpotSrcClass))
#define GST_IS_SPOT_SRC(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj),GST_TYPE_SPOT_SRC))
#define GST_IS_SPOT_SRC_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass),GST_TYPE_SPOT_SRC))

typedef struct _GstSpotSrc GstSpotSrc;
typedef struct _GstSpotSrcClass GstSpotSrcClass;

enum spot_cmd
{
  SPOT_CMD_LOGIN,
  SPOT_CMD_LOGOUT,
  SPOT_CMD_START,
  SPOT_CMD_STOP,
  SPOT_CMD_PLAY,
  SPOT_CMD_PROCESS,
  SPOT_CMD_DURATION,
  SPOT_CMD_SEEK,
  SPOT_CMD_SEARCH,
  SPOT_CMD_RESOLVE_URI,
};

struct spotify_search
{
  gchar *query;
  gint artist_nbr;
  gint artist_index;
  gint album_nbr;
  gint album_index;
};

struct spot_work
{
  GMutex *spot_mutex;
  GCond *spot_cond;
  int retval;
  sp_error error;
  gint64 opt;
  void *userdata;
  enum spot_cmd cmd;
};

#define GST_SPOT_SRC_USER(src) ((src)->user)
#define GST_SPOT_SRC_PASS(src) ((src)->pass)
#define GST_SPOT_SRC_URI(src) ((src)->uri)
#define GST_SPOT_SRC_LOGGED_IN(o) ((o)->logged_in)
#define GST_SPOT_SRC_SPOTIFY_KEY_FILE(src) ((src)->spotify_key_file)
#define GST_SPOT_SRC_RESOLVE_URI_RESULT(src) ((src)->resolve_uri_result)
#define GST_SPOT_SRC_URI_LOCATION(src) (gst_uri_get_location ((src)->uri))
#define GST_SPOT_SRC_BUFFER_TIME(src) ((src)->buffer_time)
#define GST_SPOT_SRC_ADAPTER(src) ((src)->adapter)
#define GST_SPOT_SRC_ADAPTER_MUTEX(src) ((src)->adapter_mutex)
#define GST_SPOT_SRC_ADAPTER_COND(src) ((src)->adapter_cond)
#define GST_SPOT_SRC_FORMAT(src) ((src)->format)
#define GST_SPOT_SRC_CURRENT_TRACK(o) ((o)->current_track)
#define GST_SPOT_SRC_SPOTIFY_SESSION(o) ((o)->spotify_session)


/**
 * GstSpotSrc:
 *
 * Opaque #GstSpotSrc structure.
 */
struct _GstSpotSrc {
  GstBaseSrc element;

  /*< private >*/

  gchar *user;
  gchar *pass;
  gchar *uri;
  gboolean logged_in;
  gboolean login_failed;
  gchar *spotify_key_file;
  gchar *resolve_uri_result;
  guint64 read_position;
  guint64 buffer_time;
  GstAdapter *adapter;
  GMutex *adapter_mutex;
  GCond *adapter_cond;
  sp_audioformat *format;

  GList *spot_works;
  gboolean play_token_lost;
  gboolean keep_spotify_thread;
  gboolean end_of_track;
  GMutex *process_events_mutex;
  GThread *process_events_thread;
  GCond *process_events_cond;
  gboolean spotify_thread_initiated;
  gboolean unlock_state;
  sp_track *current_track;
  sp_session *spotify_session;
  
};

struct _GstSpotSrcClass {
  GstBaseSrcClass parent_class;
};

GType gst_spot_src_get_type (void);

G_END_DECLS

#endif /* __GST_SPOT_SRC_H__ */

