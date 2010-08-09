// valac --vapidir=. --pkg spotify Spotify.vala -X -I/usr/local/include -X -L/usr/local/lib -X -lspotify

using Spotify;

public const uint8[] appkey = {
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
  0xAD
};

public static bool passed_login = false;

public static void MyConnectionError(Session session, Spotify.Error error)
{
	stderr.printf ("connection to Spotify failed: %s\n",
                 Spotify.message (error));
	//g_exit_code = 5;
}

public static void MyLoggedIn (Session session, Spotify.Error error)
{
  passed_login = true;

	if (Spotify.Error.OK != error) {
		stderr.printf ("failed to log in to Spotify: %s\n",
                   Spotify.message (error));
		//g_exit_code = 4;
		return;
	}

	// Let us print the nice message...
	User me = session.user ();
	string my_name = (me.is_loaded () ?
                    me.display_name () :
                    me.canonical_name ());

	stdout.printf ("Logged in to Spotify as user %s\n", my_name);

  session_ready(session);
}

public static void MyLoggedOut (Session session)
{
  //if (g_exit_code < 0)
  //g_exit_code = 0;
}

public static void MyNotifyMainThread (Session session)
{
  //pthread_kill(g_main_thread, SIGIO);
}

static void MyLogMessage (Session session, string data)
{
  stderr.printf ("log_message: %s\n", data);
}

public void MyMetadataUpdated(Session session)
{
}

public static void session_ready(Session session)
{
  Search search = Search.create(session, "year:2003 never", 0, 10,
                                MySearchComplete, null);
  /*
  if (!search) {
    stderr.printf ("failed to start search\n");
    //g_exit_code = 6;
    return;
  }
  */
  //g_session = session;
}

public static void MySearchComplete(Search search, void *userdata)
{
  stdout.printf ("search_complete\n");

  //if (search && SP_ERROR_OK == sp_search_error(search))
  if (Spotify.Error.OK == search.error ())
    print_search(search);
  else
    stderr.printf ("Failed to search: %s\n",
                    Spotify.message (search.error ()));

  //sp_search_release(g_search);
  //g_search = NULL;
  //terminate(session);
}

public static void print_search (Search search)
{
  int i;

  stdout.printf ("Query          : %s\n", search.query ());
  stdout.printf ("Did you mean   : %s\n", search.did_you_mean ());
  stdout.printf ("Tracks in total: %d\n", search.total_tracks ());

  stdout.printf ("\n");

  for (i = 0; i < search.num_tracks () && i < 10; ++i)
    print_track(search.track (i));

  stdout.printf ("\n");

  for (i = 0; i < search.num_albums () && i < 10; ++i)
    print_album(search.album (i));

  stdout.printf ("\n");

  for (i = 0; i < search.num_artists () && i < 10; ++i)
    print_artist(search.artist (i));

  stdout.printf ("\n");
}

public static void print_track(Track track)
{
  int duration = track.duration ();

  stdout.printf("  Track \"%s\" [%d:%02d] has %d artist(s), %d%% popularity\n",
                track.name (),
                duration / 60000,
                (duration / 1000) / 60,
                track.num_artists (),
                track.popularity ());
}

public static void print_album (Album album)
{
  stdout.printf ("  Album \"%s\" (%d)\n", album.name (), album.year ());
}

public static void print_artist (Artist artist)
{
  stdout.printf ("  Artist \"%s\"\n", artist.name ());
}

public static void terminate (Session session)
{
  Spotify.Error error;

  error = session.logout ();

  if (Spotify.Error.OK != error) {
    stderr.printf ("failed to log out from Spotify: %s\n",
                    Spotify.message (error));
    //g_exit_code = 5;
    return;
  }
}

public static int main (string[] args)
{
  SessionCallbacks callbacks = SessionCallbacks ();
  callbacks.logged_in = MyLoggedIn;
  callbacks.logged_out = MyLoggedOut;
  callbacks.metadata_updated = MyMetadataUpdated;
  callbacks.connection_error = MyConnectionError;
  callbacks.notify_main_thread = MyNotifyMainThread;
  callbacks.log_message = MyLogMessage;

  SessionConfig config = SessionConfig ();
  Spotify.Error error;
  Session session = null;

  // Sending passwords on the command line is bad in general.
  // We do it here for brevity.
  if (args.length < 3) {
    stderr. printf ("usage: %s <username> <password>\n",
                    args[0]);
    return 1;
  }

  // Always do this. It allows libspotify to check for
  // header/library inconsistencies.
  config.api_version = SPOTIFY_API_VERSION;

  // The path of the directory to store the cache. This must be specified.
  // Please read the documentation on preferred values.
  config.cache_location = "tmp";

  // The path of the directory to store the settings. This must be specified.
  // Please read the documentation on preferred values.
  config.settings_location = "tmp";

  // The key of the application. They are generated by Spotify,
  // and are specific to each application using libspotify.
  config.application_key = appkey;
  config.application_key_size = appkey.length;

  // This identifies the application using some
  // free-text string [1, 255] characters.
  config.user_agent = "spotify-session-example";

  // Register the callbacks.
  config.callbacks = &callbacks;

  error = config.init_session(&session);

  if (Spotify.Error.OK != error) {
    stderr.printf ("failed to create session: %s\n",
                   Spotify.message (error));
    return 2;
  }

  // Login using the credentials given on the command line.

  error = session.login(args[1], args[2]);

  if (Spotify.Error.OK != error) {
    stderr.printf ("failed to login: %s\n", Spotify.message (error));
    return 3;
  }

  int timeout = -1;
  while (true) {
    session.process_events(&timeout);
    Thread.usleep(1000 * timeout);
  }

  return 0;
}
