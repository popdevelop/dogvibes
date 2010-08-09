/* GStreamer
 * Copyright (C) 2009 Joel and Johan
 *
 * gstspotsrc.c:
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

#include <libspotify/api.h>
#include <gst/base/gstadapter.h>
#include <gst/gst.h>

#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <glib.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "gstspotsrc.h"
#include "config.h"

#define DEFAULT_URI "spotify://spotify:track:3odhGRfxHMVIwtNtc4BOZk"
#define DEFAULT_USER "user"
#define DEFAULT_PASS "pass"
#define DEFAULT_LOGGED_IN FALSE
#define DEFAULT_SPOTIFY_KEY_FILE "spotify_appkey.key"
#define BUFFER_TIME_MAX 50000000
#define BUFFER_TIME_DEFAULT 2000000
#define SPOTIFY_DEFAULT_SAMPLE_RATE 44100
#define SPOTIFY_DEFAULT_NUMBER_CHANNELS 2

static GstStaticPadTemplate srctemplate = GST_STATIC_PAD_TEMPLATE ("src",
    GST_PAD_SRC,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS ("audio/x-raw-int, "
        "endianness = (int) { 1234 }, "
        "signed = (boolean) { TRUE }, "
        "width = (int) 16, "
        "depth = (int) 16, "
        "rate = (int) 44100, channels = (int) 2; ")
    );

GST_DEBUG_CATEGORY_STATIC (gst_spot_src_debug);
GST_DEBUG_CATEGORY_STATIC (gst_spot_src_debug_threads);
GST_DEBUG_CATEGORY_STATIC (gst_spot_src_debug_audio);
GST_DEBUG_CATEGORY_STATIC (gst_spot_src_debug_cb);
#define GST_CAT_DEFAULT gst_spot_src_debug

/* src attributes */
enum
{
  ARG_0,
  ARG_USER,
  ARG_PASS,
  ARG_URI,
  ARG_LOGGED_IN,
  ARG_SPOTIFY_KEY_FILE,
  ARG_BUFFER_TIME
};

/* src signals */
enum
{
  SIGNAL_PLAY_TOKEN_LOST,
  LAST_SIGNAL
};

static guint gst_spot_signals[LAST_SIGNAL] = { 0 };

/* thread safe functions */
static sp_error run_spot_cmd (GstSpotSrc *spot, enum spot_cmd cmd, guint64 *retval, gint64 opt);
static void do_end_of_track (GstSpotSrc *spot);

/* libspotify */
static int spotify_cb_music_delivery (sp_session *spotify_session, const sp_audioformat *format, const void *frames, int num_frames);
static void spotify_cb_logged_in (sp_session *spotify_session, sp_error error);
static void spotify_cb_logged_out (sp_session *spotify_session);
static void spotify_cb_connection_error (sp_session *spotify_session, sp_error error);
static void spotify_cb_notify_main_thread (sp_session *spotify_session);
static void spotify_cb_log_message (sp_session *spotify_session, const char *data);
static void spotify_cb_metadata_updated (sp_session *session);
static void spotify_cb_message_to_user (sp_session *session, const char *msg);
static void spotify_cb_play_token_lost (sp_session *session);
static void spotify_cb_end_of_track (sp_session *session);
static void *spotify_thread_func (void *ptr);
static gboolean spotify_create_session (GstSpotSrc *spot);
static gboolean spotify_login (GstSpotSrc *spot);

/* basesrc stuff */
static void gst_spot_src_finalize (GObject * object);
static void gst_spot_src_set_property (GObject * object, guint prop_id, const GValue * value, GParamSpec * pspec);
static void gst_spot_src_get_property (GObject * object, guint prop_id, GValue * value, GParamSpec * pspec);
static gboolean gst_spot_src_start (GstBaseSrc * basesrc);
static gboolean gst_spot_src_stop (GstBaseSrc * basesrc);
static gboolean gst_spot_src_unlock (GstBaseSrc * basesrc);
static gboolean gst_spot_src_unlock_stop (GstBaseSrc * basesrc);
static gboolean gst_spot_src_is_seekable (GstBaseSrc * src);
static gboolean gst_spot_src_get_size (GstBaseSrc * src, guint64 * size);
static gboolean gst_spot_src_query (GstBaseSrc * src, GstQuery * query);
static GstFlowReturn gst_spot_src_create (GstBaseSrc * src, guint64 offset, guint length, GstBuffer ** buffer);

/* uri interface */
static gboolean gst_spot_src_set_spotifyuri (GstSpotSrc * src, const gchar * spotify_uri);
static gboolean gst_spot_src_uri_set_uri (GstURIHandler * handler, const gchar * uri);
static void gst_spot_src_uri_handler_init (gpointer g_iface, gpointer iface_data);
static const gchar *gst_spot_src_uri_get_uri (GstURIHandler * handler);
static gchar **gst_spot_src_uri_get_protocols (void);
static GstURIType gst_spot_src_uri_get_type (void);

/* libspotify */
static sp_session_callbacks g_callbacks = {
  &spotify_cb_logged_in,
  &spotify_cb_logged_out,
  &spotify_cb_metadata_updated,
  &spotify_cb_connection_error,
  &spotify_cb_message_to_user,
  &spotify_cb_notify_main_thread,
  &spotify_cb_music_delivery,
  &spotify_cb_play_token_lost,
  &spotify_cb_log_message,
  &spotify_cb_end_of_track
};

static uint8_t g_appkey[321];
static const size_t g_appkey_size = sizeof (g_appkey);

/* list of spotify commad work structs to be processed */
static GstSpotSrc *ugly_spot;

/*****************************************************************************/
/*** LIBSPOTIFY FUNCTIONS ****************************************************/

static void
spotify_cb_connection_error (sp_session *spotify_session, sp_error error)
{
  GST_CAT_ERROR_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Connection_error callback %s",
      sp_error_message (error));
}

static void
spotify_cb_end_of_track (sp_session *session)
{
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "End_of_track callback");
  g_mutex_lock (GST_SPOT_SRC_ADAPTER_MUTEX (ugly_spot));
  ugly_spot->end_of_track = TRUE;
  g_cond_broadcast (GST_SPOT_SRC_ADAPTER_COND (ugly_spot));
  g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (ugly_spot));
}

static void
spotify_cb_log_message (sp_session *spotify_session, const char *data)
{
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Log_message callback, data='%s'", data);
}

static void
spotify_cb_logged_in (sp_session *spotify_session, sp_error error)
{
  if (SP_ERROR_OK != error) {
    GST_CAT_ERROR_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Failed to log in to Spotify: %s", sp_error_message (error));
    ugly_spot->login_failed = TRUE;
    return;
  }

  sp_user *me = sp_session_user (spotify_session);
  const char *my_name = (sp_user_is_loaded (me) ?
                         sp_user_display_name (me) :
                         sp_user_canonical_name (me));
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Logged_in callback, user=%s", my_name);
  /* set default bitrate to audiofility */
  sp_session_preferred_bitrate (spotify_session, SP_BITRATE_320k);
  GST_SPOT_SRC_LOGGED_IN (ugly_spot) = TRUE;
}

static void
spotify_cb_logged_out (sp_session *spotify_session)
{
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Logged_out callback");
  GST_SPOT_SRC_LOGGED_IN (ugly_spot) = FALSE;
}

static void
spotify_cb_notify_main_thread (sp_session *spotify_session)
{
  GST_CAT_LOG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Notify_main_thread callback");
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_threads, ugly_spot, "Broadcast process_events_cond");
  g_cond_broadcast (ugly_spot->process_events_cond);
}

static int
spotify_cb_music_delivery (sp_session *spotify_session, const sp_audioformat *format,const void *frames, int num_frames)
{
  GstBuffer *buffer;
  guint sample_rate = format->sample_rate;
  guint channels = format->channels;
  guint bufsize = num_frames * sizeof (int16_t) * channels;
  guint availible;

  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Music_delivery callback");

  GST_SPOT_SRC_FORMAT (ugly_spot)->sample_rate = sample_rate;
  GST_SPOT_SRC_FORMAT (ugly_spot)->channels = channels;
  GST_SPOT_SRC_FORMAT (ugly_spot)->sample_type = format->sample_type;

  GST_CAT_LOG_OBJECT (gst_spot_src_debug_audio, ugly_spot, "Start %p with %d frames with size=%d", frames, num_frames, bufsize);

  if (num_frames == 0) {
    /* we have a seek */
    return 0;
  }

  buffer = gst_buffer_new_and_alloc (bufsize);

  memcpy (GST_BUFFER_DATA (buffer), (guint8*)frames, bufsize);

  g_mutex_lock (GST_SPOT_SRC_ADAPTER_MUTEX (ugly_spot));
  availible = gst_adapter_available (GST_SPOT_SRC_ADAPTER (ugly_spot));
  GST_CAT_LOG_OBJECT (gst_spot_src_debug_audio, ugly_spot, "Availiable before push = %d", availible);
  /* see if we have buffertime of audio */
  if (availible >= (GST_SPOT_SRC_BUFFER_TIME (ugly_spot)/1000000) * sample_rate * 4) {
    GST_CAT_LOG_OBJECT (gst_spot_src_debug_audio, ugly_spot, "Return 0, adapter is full = %d", availible);
    gst_buffer_unref (buffer);
    /* data is available broadcast read thread */
    g_cond_broadcast (GST_SPOT_SRC_ADAPTER_COND (ugly_spot));
    g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (ugly_spot));
    return 0;
  }

  gst_adapter_push (GST_SPOT_SRC_ADAPTER (ugly_spot), buffer);
  availible = gst_adapter_available (GST_SPOT_SRC_ADAPTER (ugly_spot));
  GST_CAT_LOG_OBJECT (gst_spot_src_debug_audio, ugly_spot, "Availiable after push = %d", availible);
  /* data is available broadcast read thread */
  g_cond_broadcast (GST_SPOT_SRC_ADAPTER_COND (ugly_spot));
  g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (ugly_spot));
  GST_CAT_LOG_OBJECT (gst_spot_src_debug_audio, ugly_spot, "Return num_frames=%d", num_frames);
  return num_frames;
}

static void
spotify_cb_metadata_updated (sp_session *session)
{
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Metadata_updated callback");
}

static void
spotify_cb_message_to_user (sp_session *session, const char *msg)
{
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Message_to_user callback, msg='%s'", msg);
}

static void
spotify_cb_play_token_lost (sp_session *session)
{
  GST_CAT_ERROR_OBJECT (gst_spot_src_debug_cb, ugly_spot, "Play_token_lost callback");
  ugly_spot->play_token_lost = TRUE;
  g_signal_emit (ugly_spot, gst_spot_signals[SIGNAL_PLAY_TOKEN_LOST], 0);
}


/*****************************************************************************/
/*** SPOTIFY THREAD FUNCTIONS ************************************************/

static void
do_end_of_track (GstSpotSrc *spot)
{
  GstPad *src_pad = gst_element_get_static_pad (GST_ELEMENT (spot), "src");
  GstPad *peer_pad = gst_pad_get_peer (src_pad);
  gst_pad_send_event (peer_pad, gst_event_new_eos ());
  spot->end_of_track = FALSE;
  gst_object_unref (peer_pad);
}

static sp_error
run_spot_cmd (GstSpotSrc *spot, enum spot_cmd cmd, guint64 *retval, gint64 opt)
{
  struct spot_work *spot_work;
  sp_error error;

  /* create work struct */
  spot_work = g_new0 (struct spot_work, 1);
  spot_work->spot_cond = g_cond_new ();
  spot_work->spot_mutex = g_mutex_new ();
  spot_work->cmd = cmd;
  spot_work->retval = 0;
  spot_work->error = SP_ERROR_OK;
  spot_work->opt = opt;

  /* add work struct to list of works */
  g_mutex_lock (spot->process_events_mutex);
  spot->spot_works = g_list_append (spot->spot_works, spot_work);
  g_mutex_unlock (spot->process_events_mutex);

  /* wait for processing */
  g_mutex_lock (spot_work->spot_mutex);
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_threads, spot, "Broadcast process_events_cond");
  g_cond_broadcast (spot->process_events_cond);
  g_cond_wait (spot_work->spot_cond, spot_work->spot_mutex);
  g_mutex_unlock (spot_work->spot_mutex);

  /* save return value */
  *retval = spot_work->retval;
  error = spot_work->error;

  /* remove work struct */
  g_cond_free (spot_work->spot_cond);
  g_mutex_free (spot_work->spot_mutex);
  g_free (spot_work);

  return error;
}

static gboolean spotify_create_session (GstSpotSrc *spot)
{
  sp_session_config config;
  sp_error error;
  FILE *keyfile;

  keyfile = fopen (GST_SPOT_SRC_SPOTIFY_KEY_FILE (spot), "r");
  if (keyfile == NULL) {
    GST_ERROR_OBJECT (spot, "Failed to open spot keyfile %s\n", 
        GST_SPOT_SRC_SPOTIFY_KEY_FILE (spot));
    return FALSE;
  }

  //FIXME error check
  fread (g_appkey, sizeof(uint8_t), g_appkey_size, keyfile);
  fclose (keyfile);

  config.application_key = g_appkey;
  config.application_key_size = g_appkey_size;
  config.api_version = SPOTIFY_API_VERSION;
  //FIXME check if these paths are appropiate
  config.cache_location = "tmp";
  config.settings_location = "tmp";
  config.user_agent = "spotify-gstreamer-src";
  config.callbacks = &g_callbacks;

  error = sp_session_init (&config, &GST_SPOT_SRC_SPOTIFY_SESSION (spot));

  if (SP_ERROR_OK != error) {
    GST_ERROR_OBJECT (spot, "Failed to create spotify_session: %s", sp_error_message (error));
    return FALSE;
  }

  GST_DEBUG_OBJECT (spot, "Created spotify session");
  return TRUE;
}

static gboolean spotify_login (GstSpotSrc *spot)
{
  sp_error error;
  if (GST_SPOT_SRC_LOGGED_IN (spot)) {
    GST_DEBUG_OBJECT (spot, "Already logged in");
    return TRUE;
  }

  /* only create session if it has not already been created */
  if (!GST_SPOT_SRC_SPOTIFY_SESSION (spot)) {
    if (!spotify_create_session (spot)) {
      GST_ERROR_OBJECT (spot, "Create_session error");
      return FALSE;
    }
  }

  GST_DEBUG_OBJECT (spot, "Trying to login");

  /* login using the credentials given on the command line */
  error = sp_session_login (GST_SPOT_SRC_SPOTIFY_SESSION (spot), GST_SPOT_SRC_USER (spot), GST_SPOT_SRC_PASS (spot));

  if (SP_ERROR_OK != error) {
    GST_ERROR_OBJECT (spot, "Failed to login: %s", sp_error_message (error));
    return FALSE;
  }

  int timeout = -1;

  sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
  while (!GST_SPOT_SRC_LOGGED_IN (spot) && !spot->login_failed) {
    usleep (10000);
    sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
  }

  spot->login_failed = FALSE;

  if (GST_SPOT_SRC_LOGGED_IN (spot)) {
    GST_DEBUG_OBJECT (spot, "Login ok!");
  } else {
    GST_DEBUG_OBJECT (spot, "Login failed!");
  }

 return TRUE;
}

/* only used to trigger sp_session_process_events when needed,
 * looks like about once a second */
static void*
spotify_thread_func (void *data)
{
  int timeout = -1;
  GTimeVal t;
  GstSpotSrc *spot = (GstSpotSrc *) data;

  while (spot->keep_spotify_thread) {
    if (GST_SPOT_SRC_SPOTIFY_SESSION (spot)) {
      sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
    }

    g_get_current_time (&t);
    g_time_val_add (&t, timeout * 1000);
    g_cond_timed_wait (spot->process_events_cond, spot->process_events_mutex, &t);
    spot->spotify_thread_initiated = TRUE;
    while (spot->spot_works) {
      struct spot_work *spot_work;
      sp_error error = SP_ERROR_INVALID_INDATA;
      spot_work = (struct spot_work *)spot->spot_works->data;
      g_mutex_lock (spot_work->spot_mutex);
      switch (spot_work->cmd) {
        case SPOT_CMD_LOGIN:
          if (!spotify_login (spot)) {
            /* error message from within function */
            break;
          }
          error = SP_ERROR_OK;
          break;
        case SPOT_CMD_LOGOUT:
	  error = sp_session_logout(GST_SPOT_SRC_SPOTIFY_SESSION (spot));
	  break;
        case SPOT_CMD_START:
          GST_DEBUG_OBJECT (spot, "Uri = %s", GST_SPOT_SRC_URI_LOCATION (spot));
          if (!spotify_login (spot)) {
            /* error message from within function */
            break;
          }

          sp_link *link = sp_link_create_from_string (GST_SPOT_SRC_URI_LOCATION (spot));

          if (!link) {
            GST_ERROR_OBJECT (spot, "Incorrect track ID:%s", GST_SPOT_SRC_URI_LOCATION (spot));
            break;
          }

          GST_SPOT_SRC_CURRENT_TRACK (spot) = sp_link_as_track (link);

          if (!GST_SPOT_SRC_CURRENT_TRACK (spot)) {
            GST_ERROR_OBJECT (spot, "Could get track from uri=%s", GST_SPOT_SRC_URI_LOCATION (spot));
            break;
          }

#if 0
          /* FIXME: why does not this work? */
          if (!sp_track_is_available (GST_SPOT_SRC_CURRENT_TRACK (spot))) {
            /* this probably happens for tracks avaiable in other countries or
               something */
            GST_ERROR_OBJECT (spot, "Track is not available, uri=%s", GST_SPOT_SRC_URI_LOCATION (spot));
            break;
          }
#endif

          sp_track_add_ref (GST_SPOT_SRC_CURRENT_TRACK (spot));
          sp_link_add_ref (link);

          sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
          while (sp_track_is_loaded (GST_SPOT_SRC_CURRENT_TRACK (spot)) == 0) {
            sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
            usleep (10000);
          }

          GST_DEBUG_OBJECT (spot, "Now playing \"%s\"", sp_track_name (GST_SPOT_SRC_CURRENT_TRACK (spot)));

          error = sp_session_player_load (GST_SPOT_SRC_SPOTIFY_SESSION (spot), GST_SPOT_SRC_CURRENT_TRACK (spot));
          if (error != SP_ERROR_OK) {
            GST_ERROR_OBJECT (spot, "Failed to load track '%s' uri=%s", sp_track_name (GST_SPOT_SRC_CURRENT_TRACK (spot)),
                (GST_SPOT_SRC_URI_LOCATION (spot)));
            break;
          }

          sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
          error = sp_session_player_play (GST_SPOT_SRC_SPOTIFY_SESSION (spot), TRUE);
          if (error != SP_ERROR_OK) {
            GST_ERROR_OBJECT (spot, "Failed to play track '%s' uri=%s", sp_track_name (GST_SPOT_SRC_CURRENT_TRACK (spot)),
                (GST_SPOT_SRC_URI_LOCATION (spot)));
            break;
          }
          break;
        case SPOT_CMD_PROCESS:
          sp_session_process_events (GST_SPOT_SRC_SPOTIFY_SESSION (spot), &timeout);
          break;

        case SPOT_CMD_PLAY:
          error = sp_session_player_play (GST_SPOT_SRC_SPOTIFY_SESSION (spot), TRUE);
          break;

        case SPOT_CMD_DURATION:
          if (GST_SPOT_SRC_CURRENT_TRACK (spot)) {
            int dur = sp_track_duration (GST_SPOT_SRC_CURRENT_TRACK (spot));
            if (dur == 0){
              error = SP_ERROR_RESOURCE_NOT_LOADED;
            }
            spot_work->retval = dur;
            

          }
	  error = SP_ERROR_OK;
          break;

        case SPOT_CMD_STOP:
          if (GST_SPOT_SRC_CURRENT_TRACK (spot)) {
            error = sp_session_player_play (GST_SPOT_SRC_SPOTIFY_SESSION (spot), FALSE);
            if (error != SP_ERROR_OK)  {
              break;
            }
            error = SP_ERROR_OK;
            sp_session_player_unload (GST_SPOT_SRC_SPOTIFY_SESSION (spot));
          }
          break;

        case SPOT_CMD_SEEK:
          if (GST_SPOT_SRC_CURRENT_TRACK (spot)) {
            error = sp_session_player_seek (GST_SPOT_SRC_SPOTIFY_SESSION (spot), spot_work->opt);
          }
          break;
        default:
          g_assert_not_reached ();
          break;

      }

      /* print all errors caught and propagate to calling thread */
      if (error != SP_ERROR_OK) {
            GST_ERROR_OBJECT (spot, "Failed with SPOT_CMD=%d, error=%d, error=%s", spot_work->cmd, error, sp_error_message (error));
      }
      spot_work->error = error;

      spot->spot_works = g_list_remove (spot->spot_works, spot->spot_works->data);
      g_mutex_unlock (spot_work->spot_mutex);
      g_cond_broadcast (spot_work->spot_cond);
    }
  }

  /* release mutex, that will be freed in finalize section */
  g_mutex_unlock (spot->process_events_mutex);

  return NULL;
}

/*****************************************************************************/
/*** BASESRC FUNCTIONS *******************************************************/

static void
_do_init (GType spotsrc_type)
{
  static const GInterfaceInfo urihandler_info = {
    gst_spot_src_uri_handler_init,
    NULL,
    NULL
  };

  g_type_add_interface_static (spotsrc_type, GST_TYPE_URI_HANDLER,
      &urihandler_info);

 /* How the debug system works:
  *
  * GST_LOG (level 5)
  * GST_INFO (level 4)
  * GST_DEBUG (level 3)
  * GST_WARNING (level 2)
  * GST_ERROR (level 1)
  *
  * To make the debug easier to follow, use a higher level for messages
  * that are printed very often. The combination of levels and categories should
  * make it easy to filter out the correct information.
  *
  * GST_DEBUG=spot*:2,spot_audio:3,spot_threads:5 for example,
  * this will give you all errors and warnings, some info on from
  * audio parts and all info for the threads
  *
  */

  GST_DEBUG_CATEGORY_INIT (gst_spot_src_debug, "SPOTSRC", 0, "spotsrc element");
  GST_DEBUG_CATEGORY_INIT (gst_spot_src_debug_threads, "SPOTSRC_THREADS", 0, "spotsrc element mutex/cond debug");
  GST_DEBUG_CATEGORY_INIT (gst_spot_src_debug_audio, "SPOTSRC_AUDIO", 0, "spotsrc element audio debug");
  GST_DEBUG_CATEGORY_INIT (gst_spot_src_debug_cb, "SPOTSRC_CB", 0, "spotsrc libspotify callbacks debug");
}

GST_BOILERPLATE_FULL (GstSpotSrc, gst_spot_src, GstBaseSrc, GST_TYPE_BASE_SRC,
    _do_init);

static void
gst_spot_src_base_init (gpointer g_class)
{

  GstElementClass *gstelement_class = GST_ELEMENT_CLASS (g_class);

  gst_element_class_set_details_simple (gstelement_class,
      "Spot Source",
      "SPOTSRC, SPOTSRC_THREADS, SPOTSRC_AUDIO, SPOTSRC_CB",
      "Spotify source element",
      "tilljoel@gmail.com (http://hackr.se) & johan.gyllenspetz@gmail.com");
  gst_element_class_add_pad_template (gstelement_class,
      gst_static_pad_template_get (&srctemplate));
}

static void
gst_spot_src_class_init (GstSpotSrcClass * klass)
{
  GObjectClass *gobject_class;
  GstBaseSrcClass *gstbasesrc_class;
  gobject_class = G_OBJECT_CLASS (klass);
  gstbasesrc_class = GST_BASE_SRC_CLASS (klass);

  gobject_class->set_property = gst_spot_src_set_property;
  gobject_class->get_property = gst_spot_src_get_property;

  gobject_class->finalize = GST_DEBUG_FUNCPTR (gst_spot_src_finalize);

  gstbasesrc_class->start = GST_DEBUG_FUNCPTR (gst_spot_src_start);
  gstbasesrc_class->stop = GST_DEBUG_FUNCPTR (gst_spot_src_stop);
  gstbasesrc_class->unlock = GST_DEBUG_FUNCPTR (gst_spot_src_unlock);
  gstbasesrc_class->unlock_stop = GST_DEBUG_FUNCPTR (gst_spot_src_unlock_stop);
  gstbasesrc_class->is_seekable = GST_DEBUG_FUNCPTR (gst_spot_src_is_seekable);
  gstbasesrc_class->get_size = GST_DEBUG_FUNCPTR (gst_spot_src_get_size);
  gstbasesrc_class->create = GST_DEBUG_FUNCPTR (gst_spot_src_create);
  gstbasesrc_class->query = GST_DEBUG_FUNCPTR (gst_spot_src_query);

  g_object_class_install_property (gobject_class, ARG_USER,
      g_param_spec_string ("user", "Username", "Username for premium spotify account",
          DEFAULT_USER, G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, ARG_PASS,
      g_param_spec_string ("pass", "Password", "Password for premium spotify account",
	  DEFAULT_PASS, G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, ARG_URI,
      g_param_spec_string ("uri", "URI", "A URI", "unknown",
          G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, ARG_LOGGED_IN,
      g_param_spec_boolean ("logged-in", "Logged in", "If logged in to spotify",
          DEFAULT_LOGGED_IN, G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, ARG_SPOTIFY_KEY_FILE,
      g_param_spec_string ("spotifykeyfile", "Spotify Key File", "Path to spotify key file",
          "unknown", G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, ARG_BUFFER_TIME,
      g_param_spec_uint64 ("buffer-time", "buffer time in us", "buffer time in us",
                      0,BUFFER_TIME_MAX,BUFFER_TIME_DEFAULT,
                      G_PARAM_READWRITE));

  gst_spot_signals[SIGNAL_PLAY_TOKEN_LOST] =
      g_signal_new ("play-token-lost", G_TYPE_FROM_CLASS (klass), G_SIGNAL_RUN_FIRST,
      0, NULL, NULL,
      g_cclosure_marshal_VOID__VOID, G_TYPE_NONE, 0);
}

static void
gst_spot_src_init (GstSpotSrc * spot, GstSpotSrcClass * g_class)
{
  GError *err;
  spot->read_position = 0;

  /* its childish to use static global variables */
  ugly_spot = GST_SPOT_SRC (spot);

  GST_SPOT_SRC_URI (spot) = g_strdup (DEFAULT_URI);

  GST_SPOT_SRC_BUFFER_TIME (spot) = BUFFER_TIME_DEFAULT;

  GST_SPOT_SRC_ADAPTER_MUTEX (spot) = g_mutex_new ();
  GST_SPOT_SRC_ADAPTER_COND (spot) = g_cond_new ();
  GST_SPOT_SRC_ADAPTER (spot) = gst_adapter_new ();

  /* initiate format to default format */
  GST_SPOT_SRC_FORMAT (spot) = g_malloc0 (sizeof (sp_audioformat));
  GST_SPOT_SRC_FORMAT (spot)->sample_rate = SPOTIFY_DEFAULT_SAMPLE_RATE;
  GST_SPOT_SRC_FORMAT (spot)->channels = SPOTIFY_DEFAULT_NUMBER_CHANNELS;
  GST_SPOT_SRC_FORMAT (spot)->sample_type = SP_SAMPLETYPE_INT16_NATIVE_ENDIAN;

  /* initiate state varables */
  spot->spot_works = NULL;
  spot->play_token_lost = FALSE;
  spot->end_of_track = FALSE;
  spot->unlock_state = FALSE;

  /* initiate user settings */
  spot->user = g_strdup (DEFAULT_USER);
  spot->pass = g_strdup (DEFAULT_PASS);
  spot->uri = g_strdup (DEFAULT_URI);
  spot->spotify_key_file = g_strdup (DEFAULT_SPOTIFY_KEY_FILE);
  spot->logged_in = DEFAULT_LOGGED_IN;
  spot->login_failed = FALSE;

  /* intiate worker thread and its state variables */
  spot->keep_spotify_thread = TRUE;
  spot->spotify_thread_initiated = FALSE;
  spot->process_events_mutex = g_mutex_new ();
  spot->process_events_cond = g_cond_new ();
  spot->process_events_thread = g_thread_create ((GThreadFunc)spotify_thread_func, spot, TRUE, &err);

  if (spot->process_events_thread == NULL) {
     GST_CAT_ERROR_OBJECT (gst_spot_src_debug_threads, spot,"G_thread_create failed: %s!", err->message );
     g_error_free (err) ;
  }

  /* make sure spotify thread is up and running, before continuing. */
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_threads, spot, "Broadcast process_events_cond");
  g_cond_broadcast (spot->process_events_cond);
  while (!spot->spotify_thread_initiated) {
    /* ugly but hey it yields right. */
    usleep (40);
    GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_threads, spot, "Broadcast process_events_cond, in loop");
    g_cond_broadcast (spot->process_events_cond);
  }
}

static void
gst_spot_src_finalize (GObject * object)
{
  GstSpotSrc *spot;

  spot = GST_SPOT_SRC (object);

  /* make thread quit */
  g_mutex_lock (spot->process_events_mutex);
  spot->keep_spotify_thread = FALSE;
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_threads, spot, "Broadcast process_events_cond");
  g_cond_broadcast (spot->process_events_cond);
  g_mutex_unlock (spot->process_events_mutex);
  g_thread_join (spot->process_events_thread);

  /* free user variables */
  g_free (spot->user);
  g_free (spot->pass);
  g_free (spot->uri);
  g_free (spot->spotify_key_file);

  g_free (spot->format);
  g_list_free (spot->spot_works);

  g_cond_free (spot->process_events_cond);
  g_mutex_free (spot->process_events_mutex);

  g_mutex_free (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
  g_cond_free (GST_SPOT_SRC_ADAPTER_COND (spot));
  g_object_unref (GST_SPOT_SRC_ADAPTER (spot));

  G_OBJECT_CLASS (parent_class)->finalize (object);

}

static void
gst_spot_src_set_property (GObject * object, guint prop_id,
    const GValue * value, GParamSpec * pspec)
{
  GstSpotSrc *spot;

  g_return_if_fail (GST_IS_SPOT_SRC (object));

  spot = GST_SPOT_SRC (object);

  switch (prop_id) {
    case ARG_USER:
      g_free (GST_SPOT_SRC_USER (spot));
      GST_SPOT_SRC_USER (spot) = g_value_dup_string (value);
      break;
    case ARG_PASS:
      g_free (GST_SPOT_SRC_PASS (spot));
      GST_SPOT_SRC_PASS (spot) = g_value_dup_string (value);
      break;
    case ARG_LOGGED_IN:
      if (g_value_get_boolean (value)) {
        //FIXME error handling
	guint64 retval;
        run_spot_cmd (spot, SPOT_CMD_LOGIN, &retval, 0);
      } else {
        //FIXME error handling
	guint64 retval;
        run_spot_cmd (spot, SPOT_CMD_LOGOUT, &retval, 0);
      }
      break;
    case ARG_URI:
      //FIXME: how do handle error from this func?
      gst_spot_src_set_spotifyuri (spot, g_value_get_string (value));
      break;
    case ARG_SPOTIFY_KEY_FILE:
      GST_SPOT_SRC_SPOTIFY_KEY_FILE (spot) = g_value_dup_string (value);
      break;
    case ARG_BUFFER_TIME:
      GST_SPOT_SRC_BUFFER_TIME (spot) = (g_value_get_uint64 (value));
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
      break;
  }
}

static void
gst_spot_src_get_property (GObject * object, guint prop_id, GValue * value,
    GParamSpec * pspec)
{
  GstSpotSrc *spot;

  g_return_if_fail (GST_IS_SPOT_SRC (object));

  spot = GST_SPOT_SRC (object);

  switch (prop_id) {
    case ARG_USER:
      g_value_set_string (value, GST_SPOT_SRC_USER (spot));
      break;
    case ARG_PASS:
      g_value_set_string (value, GST_SPOT_SRC_PASS (spot));
      break;
    case ARG_URI:
      g_value_set_string (value, GST_SPOT_SRC_URI (spot));
      break;
    case ARG_LOGGED_IN:
      g_value_set_boolean (value, GST_SPOT_SRC_LOGGED_IN (spot));
      break;
    case ARG_SPOTIFY_KEY_FILE:
      g_value_set_string (value, GST_SPOT_SRC_SPOTIFY_KEY_FILE (spot));
      break;
    case ARG_BUFFER_TIME:
      g_value_set_uint64 (value, GST_SPOT_SRC_BUFFER_TIME (spot));
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
      break;
  }
}

static GstFlowReturn
gst_spot_src_create_read (GstSpotSrc * spot, guint64 offset, guint length, GstBuffer ** buffer)
{
  if (spot->unlock_state) {
    return GST_FLOW_WRONG_STATE;
  }

  if (G_UNLIKELY (spot->read_position != offset)) {
    sp_error error;
    guint64 retval;
    /* implement spotify seek here */
    gint sample_rate = GST_SPOT_SRC_FORMAT (spot)->sample_rate;
    gint channels = GST_SPOT_SRC_FORMAT (spot)->channels;
    gint64 frames = offset / (channels * sizeof (int16_t));
    gint64 seek_usec = frames / ((float)sample_rate / 1000);

    GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_audio, spot,
        "Seek_usec = (%" G_GINT64_FORMAT ") = frames (%" G_GINT64_FORMAT ") /  sample_rate (%d/1000)",
        seek_usec, frames, sample_rate);
    GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_audio, spot,
        "Perform seek to %" G_GINT64_FORMAT " bytes and %" G_GINT64_FORMAT " usec",
        offset, seek_usec);

    error = run_spot_cmd (spot, SPOT_CMD_SEEK, &retval, seek_usec);
    if (error != SP_ERROR_OK) {
      GST_CAT_ERROR_OBJECT (gst_spot_src_debug_audio, spot, "Seek failed");
      goto create_seek_failed;
    }

    g_mutex_lock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
    gst_adapter_clear (GST_SPOT_SRC_ADAPTER (spot));
    g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));

    error = run_spot_cmd (spot, SPOT_CMD_PLAY, &retval, 0);
    if (error != SP_ERROR_OK) {
      GST_CAT_ERROR_OBJECT (gst_spot_src_debug_audio, spot, "Play failed");
      goto create_seek_failed;
    }
    spot->read_position = offset;
  }

  /* see if we have bytes to write */
  GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_audio, spot, "Length=%u offset=%" G_GINT64_FORMAT " end=%" G_GINT64_FORMAT " read_position=%" G_GINT64_FORMAT,
      length, offset, offset+length, spot->read_position);

  g_mutex_lock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
  while (1) {
    *buffer = gst_adapter_take_buffer (GST_SPOT_SRC_ADAPTER (spot), length);
    if (*buffer) {
      spot->read_position += length;
      GST_BUFFER_SIZE (*buffer) = length;
      GST_BUFFER_OFFSET (*buffer) = offset;
      GST_BUFFER_OFFSET_END (*buffer) = offset + length;
      g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
      return GST_FLOW_OK;
    }
    if (spot->end_of_track) {
      g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
      do_end_of_track (spot);
      GST_CAT_DEBUG_OBJECT (gst_spot_src_debug_audio, spot, "End of track");
      return GST_FLOW_WRONG_STATE;
    }
    //should be used in a tight conditional while
    g_cond_wait (GST_SPOT_SRC_ADAPTER_COND (spot), GST_SPOT_SRC_ADAPTER_MUTEX (spot));
    if (spot->unlock_state) {
      g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
      return GST_FLOW_WRONG_STATE;
    }
  }

  GST_CAT_ERROR_OBJECT (gst_spot_src_debug_audio, spot, "Create_read failed");

  create_seek_failed:
  return GST_FLOW_ERROR;
}

static GstFlowReturn
gst_spot_src_create (GstBaseSrc * basesrc, guint64 offset, guint length, GstBuffer ** buffer)
{
  GstSpotSrc *spot;
  GstFlowReturn ret;
  sp_error error;
  guint64 retval;

  spot = GST_SPOT_SRC (basesrc);

  if (spot->play_token_lost) {
    error = run_spot_cmd (spot, SPOT_CMD_PLAY, &retval, 0);
    if (error != SP_ERROR_OK) {
      GST_CAT_ERROR_OBJECT (gst_spot_src_debug_audio, spot, "Playtokenlost play failed");
      return error;
    }
    spot->play_token_lost = FALSE;
  }

  ret = gst_spot_src_create_read (spot, offset, length, buffer);

  return ret;
}

static gboolean
gst_spot_src_query (GstBaseSrc * basesrc, GstQuery * query)
{
  gboolean ret = TRUE;
  GstSpotSrc *spot = GST_SPOT_SRC (basesrc);
  gint samplerate = GST_SPOT_SRC_FORMAT (spot)->sample_rate;
  gint64 src_val, dest_val;

  if (!GST_SPOT_SRC_FORMAT (spot)) {
    ret = FALSE;
    goto no_format_yet;
  }

  samplerate = GST_SPOT_SRC_FORMAT (spot)->sample_rate;

  switch (GST_QUERY_TYPE (query)) {
    case GST_QUERY_POSITION:
      {
      /*FIXME
       * this one we get, answer it or propagate?
       * seems like if we answer it we are not asked
       * to convert, so i guess this is better? 

      gint64 pos;
      GstFormat format;
      gst_query_parse_position (query, &format, &pos);
      pos = GST_SPOT_SRC_READ_POS (GST_SPOT_SRC (basesrc));
      GST_INFO_OBJECT (spot, "Query_position pos=%"G_GINT64_FORMAT);
       
      */
      ret = FALSE;
      }
      break;

    case GST_QUERY_DURATION:{
      GstFormat format;
      guint64 duration;
      gint64 value;
      sp_error error;

      gst_query_parse_duration (query, &format, &value);
      /* duration in ms */
      error = run_spot_cmd (spot, SPOT_CMD_DURATION, &duration, 0);
      if (error != SP_ERROR_OK) {
        GST_CAT_ERROR_OBJECT (gst_spot_src_debug_audio, spot, "Query duration play failed");
        ret = FALSE;
      }

      /* duration in ns */
      duration = 1000000 * duration;
      switch (format) {
        case GST_FORMAT_BYTES:
          {
          guint64 duration_bytes = (duration / 1000000000) * samplerate * 4;
          GST_INFO_OBJECT (spot, "Query_duration, duration_bytes=%" G_GUINT64_FORMAT, duration_bytes);
          gst_query_set_duration (query, format, duration_bytes);
          }
          break;
        case GST_FORMAT_TIME:
          {
          guint64 duration_time = duration;
          GST_INFO_OBJECT (spot, "Query_duration, duration_time=%" G_GUINT64_FORMAT, duration_time);
          gst_query_set_duration (query, format, duration_time);
          }
          break;
        default:
          ret = FALSE;
          g_assert_not_reached ();
          break;
      }
      break;
    }

    /* FIXME: JUST FOR DEBUGING */

    case GST_QUERY_LATENCY:
      /* propagate to basesrc */
      ret = FALSE;
      GST_INFO_OBJECT (spot, "Query_latency");
      break;

    case GST_QUERY_RATE:
      /* propagate to basesrc */
      ret = FALSE;
      GST_INFO_OBJECT (spot, "Query_latency");
      break; 

    case GST_QUERY_SEEKING:
      /* propagate to basesrc */
      ret = FALSE;
      GST_INFO_OBJECT (spot, "Query_seeking");
      break; 

    case GST_QUERY_SEGMENT:
      /* propagate to basesrc */
      ret = FALSE;
      GST_INFO_OBJECT (spot, "Query_segment");
      break; 

    case GST_QUERY_FORMATS:
      /* propagate to basesrc */
      ret = FALSE;
      GST_INFO_OBJECT (spot, "Query_formats");
      break; 

    case GST_QUERY_BUFFERING:
      /* propagate to basesrc */
      ret = FALSE;
      GST_INFO_OBJECT (spot, "Query_buffering");
      break; 

    case GST_QUERY_CONVERT:
      {
        GstFormat src_fmt, dest_fmt;

        gst_query_parse_convert (query, &src_fmt, &src_val, &dest_fmt, &dest_val);

        if (src_fmt == dest_fmt) {
          dest_val = src_val;
          GST_INFO_OBJECT (spot, "Convert done, dst_fmt == src_fmt");
          goto done;
        }

        GST_INFO_OBJECT (spot, "Convert src_fmt=%s to dst_fmt=%s", gst_format_get_name (src_fmt), gst_format_get_name (dest_fmt));

        switch (src_fmt) {
        case GST_FORMAT_BYTES:
          switch (dest_fmt) {
          case GST_FORMAT_TIME:
            /* samples to time convertion 
             *   - each sample has two channels with 16 bits, 4byte
             *   - samplerate is usually 44100hz
             *   - time is in nano seconds */
            dest_val = (src_val * 1000000000) / ((float)samplerate * 4);
            GST_INFO_OBJECT (spot,"Convert src_val=%" G_GINT64_FORMAT " b, dst_val=%" G_GINT64_FORMAT " ns", src_val, dest_val);
            break;
          default:
            ret = FALSE;
            g_assert_not_reached ();
            break;
          }
          break;
        case GST_FORMAT_TIME:
          switch (dest_fmt) {
          case GST_FORMAT_BYTES:
            /* time to samples */
            dest_val = (src_val * samplerate * 4) / 1000000000;
            GST_INFO_OBJECT (spot,"Convert src_val=%" G_GINT64_FORMAT " ns, dst_val=%" G_GINT64_FORMAT " b", src_val, dest_val);
            break;
          default:
            ret = FALSE;
            g_assert_not_reached ();
            break;
          }
          break;
        default:
          ret = FALSE;
          g_assert_not_reached ();
          break;
        }
      done:
        gst_query_set_convert (query, src_fmt, src_val, dest_fmt, dest_val);
        break;
      }

    case GST_QUERY_URI:
      gst_query_set_uri (query, spot->uri);
    break;

    default:
      GST_LOG_OBJECT (spot, "Query type unknown, default, type=%s", GST_QUERY_TYPE_NAME (query));
      g_assert_not_reached ();
      break;
  }

  if (!ret) {
    GST_LOG_OBJECT (spot, "Let basesrc handle query type=%s", GST_QUERY_TYPE_NAME (query));
    ret = GST_BASE_SRC_CLASS (parent_class)->query (basesrc, query);
  }

 no_format_yet:
  if (!ret) {
    GST_DEBUG_OBJECT (spot, "Query failed");
  }

  return ret;
}

static gboolean
gst_spot_src_is_seekable (GstBaseSrc * basesrc)
{
  return TRUE;
}

static gboolean
gst_spot_src_get_size (GstBaseSrc * basesrc, guint64 * size)
{
  GstSpotSrc *spot;
  guint64 duration = 0;
  sp_error error;

  spot = GST_SPOT_SRC (basesrc);
  /* duration in ms */
  error = run_spot_cmd (spot, SPOT_CMD_DURATION, &duration, 0);
  if (error != SP_ERROR_OK) {
    GST_CAT_ERROR_OBJECT (gst_spot_src_debug, spot, "Query duration play failed");
    goto no_duration;
  }

  /* duration in ns */
  duration = 1000000 * duration;

  if (!duration) {
    GST_CAT_ERROR_OBJECT (gst_spot_src_debug_audio, spot, "No duration error");
    goto no_duration;
  }

  *size = (duration/1000000000) * 44100 * 4;
  GST_CAT_LOG_OBJECT (gst_spot_src_debug_audio, spot, "Duration=%" G_GUINT64_FORMAT " => size=%" G_GUINT64_FORMAT, duration, *size);

  return TRUE;

no_duration:
  return FALSE;
}

static gboolean
gst_spot_src_start (GstBaseSrc * basesrc)
{
  guint64 retval;
  sp_error error;

  GstSpotSrc *spot = (GstSpotSrc *) basesrc;

  GST_DEBUG_OBJECT (spot, "Start");
  error = run_spot_cmd (spot, SPOT_CMD_START, &retval, 0);
  if (error != SP_ERROR_OK) {
    GST_CAT_ERROR_OBJECT (gst_spot_src_debug, spot, "Start failed");
    return FALSE;
  }

  return TRUE;
}

static gboolean
gst_spot_src_stop (GstBaseSrc * basesrc)
{
  sp_error error;
  guint64 retval;

  GstSpotSrc *spot = (GstSpotSrc *) basesrc;

  GST_DEBUG_OBJECT (spot, "Stop");
  spot = GST_SPOT_SRC (basesrc);

  error = run_spot_cmd (spot, SPOT_CMD_STOP, &retval, 0);
  if (error != SP_ERROR_OK) {
    GST_CAT_ERROR_OBJECT (gst_spot_src_debug, spot, "Stop failed");
    return FALSE;
  }

  spot->read_position = 0;
  /* clear adapter (we are stopped and do not continue from same place) */
  g_mutex_lock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
  spot->end_of_track = FALSE;
  gst_adapter_clear (GST_SPOT_SRC_ADAPTER (spot));
  g_mutex_unlock (GST_SPOT_SRC_ADAPTER_MUTEX (spot));
  return TRUE;
}

static gboolean
gst_spot_src_unlock (GstBaseSrc *bsrc)
{
  GstSpotSrc *spot = (GstSpotSrc *) bsrc;

  spot->unlock_state = TRUE;
  GST_DEBUG_OBJECT (spot, "Unlock");
  GST_DEBUG_OBJECT (spot, "Broadcast process_events_cond - GST_SPOT_SRC_UNLOCK");
  g_cond_broadcast (GST_SPOT_SRC_ADAPTER_COND (spot));
  return TRUE;
}

static gboolean
gst_spot_src_unlock_stop (GstBaseSrc *bsrc)
{
  GstSpotSrc *spot = (GstSpotSrc *) bsrc;

  spot->unlock_state = FALSE;
  GST_DEBUG_OBJECT (spot, "Unlock stop");
  g_cond_broadcast (GST_SPOT_SRC_ADAPTER_COND (spot));
  return TRUE;
}

static gboolean
gst_spot_src_set_spotifyuri (GstSpotSrc * spot, const gchar * uri)
{
  GstState state;
  gchar *protocol = NULL;
  gchar *location;

  /* hopefully not possible */
  g_assert (uri);

  /* the element must be stopped in order to do this */
  state = GST_STATE (spot);
  if (state != GST_STATE_READY && state != GST_STATE_NULL) {
    GST_WARNING_OBJECT (spot, "Setting spotify_uri in wrong state");
    goto wrong_state;
  }

  if (!gst_uri_is_valid (uri)) {
    GST_WARNING_OBJECT (spot, "Invalid URI '%s' for spotsrc", uri);
    goto invalid_uri;
  }

  protocol = gst_uri_get_protocol (uri);
  if (strcmp (protocol, "spotify") != 0) {
     GST_WARNING_OBJECT (spot, "Setting spotify_uri with wrong protocol");
     goto wrong_protocol;
  }
  g_free (protocol);

  location = gst_uri_get_location (uri);
  if (!location) {
    GST_WARNING_OBJECT (spot, "Setting spotify_uri with wrong/no location");
    goto wrong_location;
  }

  /* we store the spotify_uri as received by the application. On Windoes this
   * should be UTF8 */
  g_free (GST_SPOT_SRC_URI (spot));

  GST_SPOT_SRC_URI (spot) = g_strdup (uri);
  
  g_object_notify (G_OBJECT (spot), "uri"); /* why? */
  gst_uri_handler_new_uri (GST_URI_HANDLER (spot), spot->uri);

  return TRUE;

  /* ERROR */
invalid_uri:

wrong_protocol:
  g_free (protocol);
wrong_state:
wrong_location:
  return FALSE;
}


/*****************************************************************************/
/*** GSTURIHANDLER INTERFACE *************************************************/

static GstURIType
gst_spot_src_uri_get_type (void)
{
  return GST_URI_SRC;
}

static gchar **
gst_spot_src_uri_get_protocols (void)
{
  static gchar *protocols[] = { "spot", NULL };

  return protocols;
}

static const gchar *
gst_spot_src_uri_get_uri (GstURIHandler * handler)
{
  GstSpotSrc *spot = GST_SPOT_SRC (handler);

  return spot->uri;
}

static gboolean
gst_spot_src_uri_set_uri (GstURIHandler * handler, const gchar * uri)
{
  GstSpotSrc *spot = GST_SPOT_SRC (handler);
  GST_DEBUG_OBJECT (spot, "New URI for interface: '%s' for spotsrc", uri);
  return gst_spot_src_set_spotifyuri (spot, uri);
}

static void
gst_spot_src_uri_handler_init (gpointer g_iface, gpointer iface_data)
{
  GstURIHandlerInterface *iface = (GstURIHandlerInterface *) g_iface;

  iface->get_type = gst_spot_src_uri_get_type;
  iface->get_protocols = gst_spot_src_uri_get_protocols;
  iface->get_uri = gst_spot_src_uri_get_uri;
  iface->set_uri = gst_spot_src_uri_set_uri;
}
