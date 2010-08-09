// compile with something like: gcc -o seek -Wall -g $(pkg-config --libs --cflags gstreamer-0.10) seek.c

// some testcode to test seek in mp3 file and in spotify element

#include <stdio.h>
#include <string.h>
#include <gst/gst.h>
#include <glib.h>

#define SPOTIFY_CMD "--spotify"
#define MP3_CMD "--mp3"

gboolean cb_timeout (gpointer data);

gint32 pos = 0;

int main (int argc, char **argv) {
    GMainLoop *loop;
    gboolean use_spotify = FALSE;
    gchar *user, *password;
    gchar *mp3_file;

    GstElement *pipeline = NULL;
    GstElement *source = NULL;
    GstElement *decoder = NULL;
    GstElement *converter = NULL;
    GstElement *resample = NULL;
    GstElement *sink = NULL;


    gst_init (&argc, &argv);
    loop = g_main_loop_new (NULL, FALSE);

    if (argc == 4 && strcmp (argv[1], SPOTIFY_CMD) == 0) {
      use_spotify = TRUE;
      user = g_strdup (argv[2]);
      password = g_strdup (argv[3]);
      g_print ("--spotify user=%s password=%s\n", user, password);

      source = gst_element_factory_make ("spot", "spotify-source");

    } else if (argc == 3 && strcmp (argv[1], MP3_CMD) == 0) {
      mp3_file = g_strdup (argv[2]);
      g_print ("--mp3 mp3_file=%s\n", mp3_file);

      source = gst_element_factory_make ("filesrc", "file-source");
      decoder = gst_element_factory_make ("mad", "mad-decoder");
      converter    = gst_element_factory_make ("audioconvert", NULL);
      resample    = gst_element_factory_make ("audioresample", NULL);

    } else {
        g_printerr ("for mp3, Usage: %s <mp3-filename> \n", argv[0]);
        g_printerr ("for spotify, Usage: %s <user> <pass>\n", argv[0]);
        return 1;
    }

    pipeline = gst_pipeline_new ("audio-player");
    sink    = gst_element_factory_make ("alsasink", "audio-output");

    if (use_spotify) {
        g_print ("-- spotifysrc link\n");
        g_object_set (G_OBJECT (source), "pass", password, NULL);
        g_object_set (G_OBJECT (source), "user", user, NULL);
        g_object_set (G_OBJECT (sink), "sync", FALSE, NULL);

        gst_bin_add_many (GST_BIN (pipeline), source, sink, NULL);
        gst_element_link_many (source, sink, NULL);
    } else {
        g_print ("-- mp3 link\n");
        g_object_set (G_OBJECT (source), "location", mp3_file, NULL);
        gst_bin_add_many (GST_BIN (pipeline), source, decoder, converter, resample, sink, NULL);
        gst_element_link_many (source, decoder, converter, resample, sink, NULL);
    }

    g_print ("Now playing\n");
    gst_element_set_state (pipeline, GST_STATE_PLAYING);

    // random seek every 3 seconds
    g_timeout_add (6 * 1000, cb_timeout, pipeline);

    g_print ("running...\n");
    g_main_loop_run (loop);

    g_print ("returned, stopping playback\n");
    gst_element_set_state (pipeline, GST_STATE_NULL);

    g_print ("deleting pipeline\n");
    gst_object_unref (GST_OBJECT (pipeline));

    g_free (user);
    g_free (password);
    g_free (mp3_file);
    return 0;
}

gboolean cb_timeout (gpointer data) {
    GstElement *pipeline = (GstElement *) data;
    GstFormat fmt = GST_FORMAT_BYTES;
    gboolean test;
    gint64 len;

    puts ("timeout called");

    test = gst_element_query_duration (
        pipeline, &fmt, &len
    );
    guint64 bytes = g_random_int_range (0,len);
    g_print ("duration = %lld, seek to %lld\n",len, bytes);

    test = gst_element_seek (
        pipeline,
        1.0,
        GST_FORMAT_BYTES,
        GST_SEEK_FLAG_FLUSH,
        GST_SEEK_TYPE_SET,
        bytes,
        GST_SEEK_TYPE_NONE,
        -1
        );
    printf ("seek to %lld bytes res=%d\n", bytes,test);


    return TRUE;
}

