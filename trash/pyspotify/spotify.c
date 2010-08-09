#include <Python.h>
#include <spotify/api.h>
#include <stdbool.h>

static const uint8_t g_appkey[] = {
  0x01, 0x0B, 0x26, 0x66, 0xEA, 0x7A, 0x82, 0x83, 0x61, 0x73, 0x78, 0xC3, 0xAC, 0x7E, 0xF6, 0x62,
  0x6C, 0xF4, 0xF8, 0xCE, 0xF1, 0x61, 0xB7, 0x70, 0x54, 0xB3, 0xE8, 0x8E, 0x3E, 0x32, 0x68, 0x98,
  0xEF, 0x63, 0x42, 0xAC, 0x7E, 0x5B, 0x7C, 0x7C, 0x58, 0xA9, 0x97, 0x5B, 0xEA, 0xBC, 0x9C, 0xFB,
  0x2A, 0x34, 0xA5, 0x17, 0xBD, 0x3B, 0xF2, 0x6A, 0xD2, 0xB4, 0x5F, 0x1C, 0x30, 0x52, 0x49, 0x2C,
  0x03, 0x71, 0xE1, 0x1D, 0xE5, 0xB1, 0x93, 0xEF, 0x6C, 0x38, 0xAB, 0x62, 0x40, 0x9B, 0x10, 0x6A,
  0x31, 0x24, 0x27, 0x77, 0x40, 0x1D, 0x06, 0x1B, 0xE2, 0xA5, 0xA3, 0x55, 0x57, 0x57, 0xD5, 0x12,
  0xAC, 0xDE, 0xB0, 0xBA, 0x48, 0xC3, 0x22, 0x4D, 0xA9, 0x13, 0x13, 0xD9, 0x22, 0x02, 0x87, 0x25,
  0x05, 0x51, 0xEA, 0x91, 0x5A, 0xAE, 0xCA, 0x73, 0x23, 0x0F, 0xC7, 0x7D, 0xCF, 0x80, 0x03, 0x8A,
  0x6F, 0x92, 0xC7, 0x75, 0x21, 0xEC, 0x0E, 0xBE, 0xB7, 0xE3, 0x7C, 0x7F, 0x49, 0x69, 0x30, 0x71,
  0xC9, 0x8A, 0x61, 0x1B, 0x50, 0xAC, 0x92, 0x88, 0x9C, 0x17, 0x21, 0x5F, 0x32, 0xF4, 0xD2, 0x15,
  0x7F, 0xF8, 0x86, 0x11, 0x25, 0x02, 0x53, 0xAA, 0x8D, 0x0C, 0x51, 0x13, 0x51, 0x17, 0x02, 0x10,
  0x86, 0xED, 0x68, 0xCD, 0x19, 0x22, 0x4B, 0x3F, 0xA3, 0x73, 0x6F, 0xD9, 0xDD, 0xAE, 0xAF, 0x85,
  0xD6, 0xF3, 0x08, 0xDB, 0xA7, 0x49, 0x3B, 0x56, 0xD1, 0x77, 0xC8, 0x9B, 0xCA, 0x06, 0x1E, 0xB0,
  0x4A, 0xE9, 0x92, 0xAC, 0x04, 0xAB, 0xDF, 0x90, 0x39, 0x0F, 0xD3, 0xD7, 0x16, 0xEF, 0xA5, 0xFF,
  0xDC, 0x81, 0x3F, 0x09, 0x8D, 0x3D, 0xAC, 0x92, 0x86, 0x21, 0x9F, 0x72, 0x12, 0xA5, 0x1A, 0x6A,
  0xB3, 0x09, 0xEA, 0xCB, 0x3C, 0xCE, 0x73, 0xBD, 0x91, 0x1D, 0x99, 0xCE, 0x45, 0xB6, 0x6F, 0x7E,
  0x6A, 0x99, 0x33, 0x6D, 0x10, 0x11, 0x3F, 0xB4, 0x3E, 0x98, 0xD2, 0x37, 0xDD, 0x35, 0xB9, 0x59,
  0x5E, 0x41, 0x55, 0x9C, 0xC2, 0xFE, 0x72, 0x75, 0x37, 0xEA, 0x7A, 0xCF, 0x4F, 0x49, 0x37, 0x31,
  0xA4, 0x51, 0xC5, 0x0F, 0x42, 0x19, 0x7E, 0x43, 0x71, 0x43, 0x97, 0xE7, 0x76, 0x79, 0xBD, 0x2F,
  0x65, 0x7D, 0x9C, 0x3D, 0x97, 0x7A, 0x76, 0xE0, 0xAE, 0xED, 0x96, 0x74, 0xD5, 0x01, 0x41, 0x61,
  0xAD,
};

static const size_t g_appkey_size = sizeof (g_appkey);

/* global stuff */
static sp_session *session;
static bool loggedin = false;

static void logged_in(sp_session *session, sp_error error)
{
  if (SP_ERROR_OK != error) {
    printf("failed to log in to Spotify: %s\n",
            sp_error_message(error));
    return;
  }

  sp_user *me = sp_session_user(session);
  const char *my_name = (sp_user_is_loaded(me) ?
                         sp_user_display_name(me) :
                         sp_user_canonical_name(me));

  printf("Logged in to Spotify as user %s\n", my_name);
  loggedin = true;
}

static void logged_out(sp_session *session)
{
}

static sp_session_callbacks g_callbacks = {
  &logged_in,
  &logged_out,
  NULL, //&spotify_cb_metadata_updated,
  NULL, //&spotify_cb_connection_error,
  NULL, //&spotify_cb_message_to_user,
  NULL, //&spotify_cb_notify_main_thread,
  NULL, //&spotify_cb_music_delivery,
  NULL, //&spotify_cb_play_token_lost,
  NULL, //&spotify_cb_log_message
};

static PyObject *
spotifydogvibes_login(PyObject *self, PyObject *args, PyObject * kwargs)
{
  char *user;
  char *pass;

  if (!PyArg_ParseTuple(args, "ss", &user, &pass)){
    return NULL;
  }

  printf("Trying to log in user=%s pass=%s\n", user, pass);

  sp_session_config config;
  sp_error error;

  config.api_version = SPOTIFY_API_VERSION;
  config.cache_location = "tmp";
  config.settings_location = "tmp";
  config.application_key = g_appkey;
  config.application_key_size = g_appkey_size;
  config.user_agent = "dogvibes";

  config.callbacks = &g_callbacks;
  error = sp_session_init(&config, &session);

  if (SP_ERROR_OK != error) {
    printf("failed to create session: %s\n",
           sp_error_message(error));
    return Py_BuildValue("i", 2);
  }

  error = sp_session_login(session, user, pass);

  int timeout = -1;
  while (!loggedin) {
    sp_session_process_events(session, &timeout);
    sleep(0.1);
  }

  if (SP_ERROR_OK != error) {
    printf("failed to login: %s\n",
           sp_error_message(error));
    return Py_BuildValue("i", 3);
  }

  return Py_BuildValue("i", 1);
}

static void search_complete(sp_search *search, void *userdata)
{
  printf("Search was complete\n");
}

static sp_search *search;

static PyObject *
spotifydogvibes_search(PyObject *self, PyObject *args, PyObject * kwargs)
{
  int i;
  char *query;
  PyObject *ret;
  int timeout = -1;

  if (!PyArg_ParseTuple(args, "s", &query)){
    Py_BuildValue("{s,s}");;
  }

  search = sp_search_create(session, query, 0, 100,
                            &search_complete, NULL);

  if (!search) {
    return NULL;
  }

  while (!sp_search_is_loaded(search)) {
    sp_session_process_events(session, &timeout);
    sleep(0.1);
  }

  ret = Py_BuildValue("[]");

  for (i = 0; i < sp_search_num_tracks(search) && i < 100; ++i) {
    sp_track *track = sp_search_track(search, i);
    PyObject *trackinfo = Py_BuildValue("{s,s}", "title", sp_track_name(track));
    PyDict_Update(trackinfo, Py_BuildValue("{s,i}", "duration", sp_track_duration(track)));

    sp_album *album = sp_track_album(track);
    PyDict_Update(trackinfo, Py_BuildValue("{s,s}", "album", sp_album_name(album)));

    sp_artist *artist = sp_track_artist(track, 0);
    PyDict_Update(trackinfo, Py_BuildValue("{s,s}", "artist", sp_artist_name(artist)));

    char uri[256];
    sp_link *link = sp_link_create_from_track(track, 0);
    sp_link_as_string(link, uri, sizeof(uri));
    PyDict_Update(trackinfo, Py_BuildValue("{s,s}", "uri", uri));
    PyList_Append(ret, trackinfo);
  }

  sp_search_release(search);

  return ret;
}

static PyObject*
spotifydogvibes_create_track_from_uri(PyObject *self, PyObject *args, PyObject * kwargs)
{
  char *uri;

  if (!PyArg_ParseTuple(args, "s", &uri)){
    return NULL;
  }

  sp_link *link = sp_link_create_from_string(uri);
  if (link == NULL) {
    return Py_BuildValue("{}");
  }

  sp_track *track = sp_link_as_track(link);

  int timeout = -1;
  while (!sp_track_is_loaded(track)) {
    sp_session_process_events(session, &timeout);
    sleep(0.1);
  }

  sp_album *album = sp_track_album(track);
  sp_artist *artist = sp_track_artist(track, 0);

  PyObject *trackinfo = Py_BuildValue("{s,s}", "title", sp_track_name(track));
  PyDict_Update(trackinfo, Py_BuildValue("{s,i}", "duration", sp_track_duration(track)));
  PyDict_Update(trackinfo, Py_BuildValue("{s,s}", "album", sp_album_name(album)));
  PyDict_Update(trackinfo, Py_BuildValue("{s,s}", "artist", sp_artist_name(artist)));
  PyDict_Update(trackinfo, Py_BuildValue("{s,s}", "uri", uri));

  return trackinfo;
}

static PyMethodDef SpamMethods[] = {

  {"login", spotifydogvibes_login, METH_VARARGS,
   "Login to spotify."},
  {"search", spotifydogvibes_search, METH_VARARGS,
   "Perform a search on spotify."},
  {"create_track_from_uri", spotifydogvibes_create_track_from_uri, METH_VARARGS,
   "Create track from spotify uri."},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initspotifydogvibes(void)
{
  (void) Py_InitModule("spotifydogvibes", SpamMethods);
}
