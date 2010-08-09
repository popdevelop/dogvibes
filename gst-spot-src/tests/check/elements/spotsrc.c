/* GStreamer
 * unit test for spot
 *
 * Copyright (C) <2010> Johan Gyllenspez
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

#include <unistd.h>
#include <gst/check/gstcheck.h>

/* For ease of programming we use globals to keep refs for our floating
 * src and sink pads we create; otherwise we always have to do get_pad,
 * get_peer, and then remove references in every test function */
static GstPad *mysinkpad;

#define CAPS_TEMPLATE_STRING            \
    "audio/x-raw-int, "                 \
    "channels = (int) 2, "              \
    "rate = (int) 44100, "              \
    "endianness = (int) { 1234 }, "     \
    "width = (int) 16, "                \
    "depth = (int) 16, "                \
    "signed = (bool) TRUE"

#define SPOTIFY_URI "spotify://spotify:track:0E4rbyLYVCGLu75H3W6O67"
#define SPOTIFY_URI_2 "spotify://spotify:track:13GSFj7uIxqL9eNItNob3p"
#define SPOTIFY_URI_ERROR "spotify://spotify:track:deadbeefdeadbeefdeadbeef"

#define SPOTIFY_USER "user"
#define SPOTIFY_PASS "pass"

/* seems that some songs are availible when we seek, but we are not able to
 * load them, for example the awesome song by reflection eternal:
 * In This World - Amended Album Version uri=spotify:track:2FEyrK5QyboZLgfG6BPmYM
 */
#define SPOTIFY_URI_TALIB_KWELI "spotify://spotify:track:2FEyrK5QyboZLgfG6BPmYM"
#define SPOTIFY_URI_JUST_BAD "spotify://spotify:track:2FEyaaaaaaaaaaaaaaaa"
/* FIXME: add test with longer uri, add two more a's and it fails */

static GstStaticPadTemplate sinktemplate = GST_STATIC_PAD_TEMPLATE ("sink",
    GST_PAD_SINK,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS (CAPS_TEMPLATE_STRING)
    );

guint probe_id;

static gboolean
buffer_counter (GstObject * pad, GstBuffer * buffer, guint * p_num_eos);

static GstElement *
setup_spot (void)
{
  GstElement *spot;

  spot = gst_check_setup_element ("spot");
  g_object_set (G_OBJECT (spot), "uri", SPOTIFY_URI, NULL);
  g_object_set (G_OBJECT (spot), "user", SPOTIFY_USER, NULL);
  g_object_set (G_OBJECT (spot), "pass", SPOTIFY_PASS, NULL);
  g_object_set (G_OBJECT (spot), "spotifykeyfile", "dogspotify_appkey.key", NULL);
  g_object_set (G_OBJECT (spot), "logged-in", TRUE, NULL);
  mysinkpad = gst_check_setup_sink_pad (spot, &sinktemplate, NULL);
  gst_pad_set_active (mysinkpad, TRUE);

  probe_id = gst_pad_add_buffer_probe (mysinkpad,
      G_CALLBACK (buffer_counter), NULL);

  return spot;
}

static void
cleanup_spot (GstElement * spot)
{
  g_list_foreach (buffers, (GFunc) gst_mini_object_unref, NULL);
  g_list_free (buffers);
  buffers = NULL;

  gst_pad_remove_buffer_probe (mysinkpad, probe_id);
  gst_pad_set_active (mysinkpad, FALSE);
  gst_check_teardown_sink_pad (spot);
  gst_check_teardown_element (spot);
}

static void
play_and_verify_buffers (GstElement *spot, int num_buffs)
{
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_PLAYING) == GST_STATE_CHANGE_SUCCESS,
               "could not set to playing");

  g_mutex_lock (check_mutex);
  while (g_list_length (buffers) < num_buffs) {
    g_cond_wait (check_cond, check_mutex);
  }

  printf("length =%d\n", g_list_length(buffers));

  g_mutex_unlock (check_mutex);

  g_list_foreach (buffers, (GFunc) gst_mini_object_unref, NULL);
  g_list_free (buffers);
  buffers = NULL;
}

static gboolean
eos_event_counter (GstObject * pad, GstEvent * event, guint * p_num_eos)
{
  fail_unless (event != NULL);
  fail_unless (GST_IS_EVENT (event));

  if (GST_EVENT_TYPE (event) == GST_EVENT_EOS) {
    *p_num_eos += 1;
    printf ("# ");
  }

  return TRUE;
}

static gboolean
buffer_counter (GstObject * pad, GstBuffer * buf, guint * p_num_eos)
{
  fail_unless (buf != NULL);
  fail_unless (GST_IS_BUFFER (buf));

  printf (".");
  fflush (stdout);
  return TRUE;
}

GST_START_TEST (test_login_and_play_pause)
{
  GstElement *spot;

  g_print ("*** STARTING - TEST LOGIN PLAY PAUSE\n");
  g_print ("***\n");
  g_print ("*** each buffer is seen as '.'\n\n");
  spot = setup_spot ();

  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("PAUSE\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_PAUSED) == GST_STATE_CHANGE_SUCCESS,
               "could not pause element");
  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("PAUSE\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_PAUSED) == GST_STATE_CHANGE_SUCCESS,
               "could not pause element");
  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("PAUSE\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_PAUSED) == GST_STATE_CHANGE_SUCCESS,
               "could not pause element");
  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("STOP\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_NULL) == GST_STATE_CHANGE_SUCCESS,
               "could not stop element");

  /* cleanup */
  cleanup_spot (spot);
  g_print ("\n^^^ END - TEST LOGIN PLAY PAUSEEVENTS\n\n\n");
}
GST_END_TEST;

GST_START_TEST (test_eos_events_push)
{
  GstStateChangeReturn state_ret;
  GstElement *src, *sink, *pipe;
  GstMessage *msg;
  GstBus *bus;
  GstPad *srcpad;
  guint probe, num_eos = 0;

  g_print ("*** STARTING - TEST EOS EVENTS\n");
  g_print ("***\n");
  g_print ("*** num-buffers=8, seen as '.'\n");
  g_print ("*** wait for one EOS event, seen as '#'\n\n");

  pipe = gst_pipeline_new ("pipeline");
  fail_unless (pipe != NULL, "Failed to create pipeline element");
  sink = gst_element_factory_make ("fakesink", "sink");
  fail_unless (sink != NULL, "Failed to create sink element");
  src = gst_element_factory_make ("spot", "src");
  fail_unless (src != NULL, "Failed to create src element");

  g_object_set (G_OBJECT (src), "user", SPOTIFY_USER, NULL);
  g_object_set (G_OBJECT (src), "pass", SPOTIFY_PASS, NULL);
  g_object_set (G_OBJECT (src), "uri", SPOTIFY_URI, NULL);
  g_object_set (G_OBJECT (src), "spotifykeyfile", "dogspotify_appkey.key", NULL);
  g_object_set (G_OBJECT (src), "logged-in", TRUE, NULL);

  g_assert (pipe != NULL);
  g_assert (sink != NULL);
  g_assert (src != NULL);

  fail_unless (gst_bin_add (GST_BIN (pipe), src) == TRUE);
  fail_unless (gst_bin_add (GST_BIN (pipe), sink) == TRUE);

  fail_unless (gst_element_link (src, sink) == TRUE);

  g_object_set (sink, "can-activate-push", TRUE, NULL);
  g_object_set (sink, "can-activate-pull", FALSE, NULL);

  //g_object_set (src, "can-activate-push", TRUE, NULL);
  //g_object_set (src, "can-activate-pull", FALSE, NULL);
  g_object_set (src, "num-buffers", 8, NULL);

  srcpad = gst_element_get_pad (src, "src");
  fail_unless (srcpad != NULL);

  probe_id = gst_pad_add_buffer_probe (srcpad,
      G_CALLBACK (buffer_counter), NULL);
  probe = gst_pad_add_event_probe (srcpad,
      G_CALLBACK (eos_event_counter), &num_eos);

  bus = gst_element_get_bus (pipe);
  printf ("PLAY");
  gst_element_set_state (pipe, GST_STATE_PLAYING);
  state_ret = gst_element_get_state (pipe, NULL, NULL, -1);
  fail_unless (state_ret == GST_STATE_CHANGE_SUCCESS);

  msg = gst_bus_poll (bus, GST_MESSAGE_EOS | GST_MESSAGE_ERROR, -1);
  fail_unless (msg != NULL);
  fail_unless (GST_MESSAGE_TYPE (msg) != GST_MESSAGE_ERROR);
  fail_unless (GST_MESSAGE_TYPE (msg) == GST_MESSAGE_EOS);

  fail_unless (num_eos == 1);

  gst_element_set_state (pipe, GST_STATE_NULL);
  gst_element_get_state (pipe, NULL, NULL, -1);

  fail_unless (num_eos == 1);
  printf ("EOS\n");

  gst_pad_remove_event_probe (srcpad, probe);
  gst_pad_remove_buffer_probe (srcpad, probe_id);
  gst_object_unref (srcpad);
  gst_message_unref (msg);
  gst_object_unref (bus);
  gst_object_unref (pipe);
  g_print ("\n^^^ END - TEST EOS EVENTS\n\n\n");
}

GST_END_TEST;

GST_START_TEST (test_change_track)
{
  GstElement *spot;

  spot = setup_spot ();

  g_print ("*** STARTING - CHANGE TRACK\n");
  g_print ("***\n\n");
  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("STOP\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_NULL) == GST_STATE_CHANGE_SUCCESS,
               "could not stop element");
  g_object_set (G_OBJECT (spot), "uri", SPOTIFY_URI_2, NULL);
  g_print ("*** set new track\n");
  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("STOP\n");

  /* cleanup */
  cleanup_spot (spot);
  g_print ("\n^^^ END - CHANGE TRACK\n\n\n");
}
GST_END_TEST;

static gboolean
get_element_position (GstElement *elem)
{
  GstFormat fmt = GST_FORMAT_TIME;
  gint64 pos;

  if (gst_element_query_position (elem, &fmt, &pos)) {
    return pos;
  }
  return -1;
}

GST_START_TEST (test_pause_and_duration)
{
  GstElement *spot;

  g_print ("*** STARTING - TEST PAUSE AND DURATION\n");
  g_print ("***\n");
  g_print ("*** each buffer is seen as '.'\n\n");
  spot = setup_spot ();

  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("PAUSE\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_PAUSED) == GST_STATE_CHANGE_SUCCESS,
               "could not pause element");
  //get duration
  fail_if (0 == get_element_position(spot));

  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("PAUSE\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_PAUSED) == GST_STATE_CHANGE_SUCCESS,
               "could not pause element");
  //get duration
  fail_if (0 == get_element_position(spot));

  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("STOP\n");
  fail_unless (gst_element_set_state (spot,
                                      GST_STATE_NULL) == GST_STATE_CHANGE_SUCCESS,
               "could not stop element");

  /* cleanup */

  cleanup_spot (spot);
  g_print ("\n^^^ END - CHANGE TRACK\n\n\n");
}
GST_END_TEST;

GST_START_TEST (test_seek)
{
  GstElement *spot;
  gint64 duration;
  GstFormat format = GST_FORMAT_TIME;

  spot = setup_spot ();

  g_print ("*** STARTING - TEST SEEK\n");
  g_print ("***\n\n");
  fail_unless (gst_element_query_duration (spot, &format, &duration));
  g_print ("PLAY");
  play_and_verify_buffers (spot, 10);
  g_print ("STOP\n");
  fail_unless (gst_element_query_duration (spot, &format, &duration));

  gst_element_seek_simple (spot, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH | GST_SEEK_FLAG_KEY_UNIT, GST_SECOND * 1);

  /* FIXME: THIS LOCKS SINK. */
  /* play_and_verify_buffers (spot, 10); */

  /* gst_element_seek_simple (spot, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH, GST_SECOND * 10); */
  /* gst_element_seek_simple (spot, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH, GST_SECOND * 100); */

  /* play_and_verify_buffers (spot, 10); */

  /* gst_element_seek_simple (spot, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH, GST_SECOND * 10); */
  /* gst_element_seek_simple (spot, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH, duration); */
  /* gst_element_seek_simple (spot, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH, duration + GST_SECOND * 10); */

  /* cleanup */
  cleanup_spot (spot);
  g_print ("\n^^^ END - SEEK\n\n\n");
}
GST_END_TEST;

GST_START_TEST (test_login_and_play_bad_uri)
{
  GstElement *spot;

  /* src_start should not success with bad uri */

  g_print ("*** STARTING - TEST LOGIN PLAY BAD URI\n");

  spot = gst_check_setup_element ("spot");
  g_print ("*** uri=%s\n\n", SPOTIFY_URI_JUST_BAD);
  g_object_set (G_OBJECT (spot), "uri", SPOTIFY_URI_JUST_BAD, NULL);
  g_object_set (G_OBJECT (spot), "user", SPOTIFY_USER, NULL);
  g_object_set (G_OBJECT (spot), "pass", SPOTIFY_PASS, NULL);
  g_object_set (G_OBJECT (spot), "spotifykeyfile", "dogspotify_appkey.key", NULL);
  g_object_set (G_OBJECT (spot), "logged-in", TRUE, NULL);
  mysinkpad = gst_check_setup_sink_pad (spot, &sinktemplate, NULL);
  gst_pad_set_active (mysinkpad, TRUE);
  probe_id = gst_pad_add_buffer_probe (mysinkpad,
      G_CALLBACK (buffer_counter), NULL);

  g_print ("TRY PLAY\n");
  /* should not be able to play with faulty URI */
  fail_if (gst_element_set_state (spot,
                              GST_STATE_PLAYING) == GST_STATE_CHANGE_SUCCESS,
                              "could not set to playing");

  cleanup_spot (spot);


  spot = gst_check_setup_element ("spot");
  g_print ("*** uri=%s\n", SPOTIFY_URI_TALIB_KWELI);
  g_object_set (G_OBJECT (spot), "uri", SPOTIFY_URI_TALIB_KWELI, NULL);
  g_object_set (G_OBJECT (spot), "user", SPOTIFY_USER, NULL);
  g_object_set (G_OBJECT (spot), "pass", SPOTIFY_PASS, NULL);
  g_object_set (G_OBJECT (spot), "spotifykeyfile", "dogspotify_appkey.key", NULL);
  g_object_set (G_OBJECT (spot), "logged-in", TRUE, NULL);
  mysinkpad = gst_check_setup_sink_pad (spot, &sinktemplate, NULL);
  gst_pad_set_active (mysinkpad, TRUE);
  probe_id = gst_pad_add_buffer_probe (mysinkpad,
      G_CALLBACK (buffer_counter), NULL);

  /* spotify is showing us some upcoming hits here? */
  g_print ("TRY PLAY\n");
  fail_if (gst_element_set_state (spot,
                              GST_STATE_PLAYING) == GST_STATE_CHANGE_SUCCESS,
                              "could not set to playing");

  cleanup_spot (spot);
  g_print ("\nEND - TEST LOGIN PLAY BAD URI\n\n\n");
}
GST_END_TEST;

GST_START_TEST (test_user_pass)
{
  /* so we dont have run all tests */
  g_print ("*** STARTING - USER/PASS CHANGE?\n");
  gboolean unchanged = strcmp (SPOTIFY_USER, "user") == 0 && strcmp (SPOTIFY_PASS, "pass") == 0;
  fail_if (unchanged,
           "You are using wrong defines in %s, rest of the test should fail/timeout\n"
           "user=%s\npass=%s", __FILE__,
           SPOTIFY_USER, SPOTIFY_PASS);
  g_assert (!unchanged);
  g_print ("^^^ END - USER/PASS CHANGED\n\n\n");
}
GST_END_TEST;

GST_START_TEST (test_attributes)
{
  /* so we dont have run all tests */
  g_print ("\n*** STARTING - TEST ATTRIBUTES\n");
  g_print ("\n^^^ END - TEST ATTRIBUTES\n\n\n");
}
GST_END_TEST;

static Suite *
spot_suite (void)
{
  Suite *s = suite_create ("spot");
  TCase *tc_chain = tcase_create ("general");

  suite_add_tcase (s, tc_chain);
  tcase_set_timeout (tc_chain, 20);

  tcase_add_test (tc_chain, test_user_pass);
  tcase_add_test (tc_chain, test_pause_and_duration);
  tcase_add_test (tc_chain, test_eos_events_push);
  tcase_add_test (tc_chain, test_login_and_play_pause);
  tcase_add_test (tc_chain, test_login_and_play_bad_uri);
  tcase_add_test (tc_chain, test_change_track);
  tcase_add_test (tc_chain, test_seek);
  tcase_add_test (tc_chain, test_attributes);

  return s;
}

int
main (int argc, char **argv)
{
  int nf;

  Suite *s = spot_suite ();
  SRunner *sr = srunner_create (s);

  gst_check_init (&argc, &argv);

  srunner_run_all (sr, CK_NORMAL);
  nf = srunner_ntests_failed (sr);
  srunner_free (sr);

  return nf;
}
