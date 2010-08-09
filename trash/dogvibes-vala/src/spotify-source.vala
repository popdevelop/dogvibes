using Gst;
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
public static bool search_done = true;
public static weak Session session;

public static void MyLoggedIn (Session session, Spotify.Error error)
{
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

  passed_login = true;

  //session_ready(session);
}

public static void PollMe (Session session)
{
  int timeout;
  //session.process_events(&timeout);
  stdout.printf ("do you poll me?");
}

public class SpotifySource : GLib.Object, Source, SingleSource {
  public Bin bin;
  public string user;
  public string pass;

  public weak Amplifier owner { get; set; }

  private Element spotify;
  private bool created;

  public static GLib.List<Track> tracks;

  public SpotifySource (string user, string pass) {
    this.user = user;
    this.pass = pass;
  }

  construct {
    owner = null;
    created = false;

    /*
     * setup the Spotify library
     */
    SessionConfig config = SessionConfig ();
    Spotify.Error error;

    SessionCallbacks callbacks = SessionCallbacks ();
    callbacks.logged_in = MyLoggedIn;
    /*
    callbacks.logged_out = MyLoggedOut;
    callbacks.metadata_updated = MyMetadataUpdated;
    callbacks.connection_error = MyConnectionError;

    callbacks.log_message = MyLogMessage;
    */
    callbacks.notify_main_thread = PollMe;


    config.api_version = SPOTIFY_API_VERSION;
    config.cache_location = "tmp";
    config.settings_location = "tmp";
    config.application_key = appkey;
    config.application_key_size = appkey.length;
    config.user_agent = "dogvibes";
    config.callbacks = &callbacks;

    error = config.init_session(&session);

    if (Spotify.Error.OK != error) {
      stderr.printf ("failed to create session: %s\n",
                     Spotify.message (error));
      //return 2;
    }

    //    error = session.login(user, pass);
    error = session.login("gyllen", "bobidob10");

    if (Spotify.Error.OK != error) {
      stderr.printf ("failed to login: %s\n", Spotify.message (error));
      //return 3;
    }

    int timeout = -1;
    while (!passed_login) {
      session.process_events(&timeout);
      Thread.usleep(100 * timeout);
    }

  }

  public Bin get_src () {
    /* Ugly this should be solved when we start using decodebin */
    if (!created) {
      bin = new Bin("spotifybin");
      this.spotify = ElementFactory.make ("spotify", "spotify");
      stdout.printf ("Logging on to Spotify\n");
      spotify.set ("user", user);
      spotify.set ("pass", pass);
      spotify.set ("buffer-time", (int64) 100000000);
      bin.add (this.spotify);
      GhostPad gpad = new GhostPad ("src", this.spotify.get_static_pad("src"));
      bin.add_pad (gpad);
      created = true;
    }
    return bin;
  }

  public static void MySearchComplete(Search search, void *userdata) {
    if (Spotify.Error.OK != search.error ()) {
      stderr.printf ("Failed to search: %s\n",
                     Spotify.message (search.error ()));
    }

    int i;
    Track track;
    for (i = 0; i < search.num_tracks () && i < 100; ++i) {
      track = new Track ();
      Spotify.Track strack = search.track (i);
      Spotify.Album album = strack.album ();
      Spotify.Artist artist = strack.artist (0);

      track.name = strack.name ();
      track.artist = artist.name ();
      track.album = album.name ();
      track.duration = strack.duration ().to_string ();

      Spotify.Link link;
      char[] uri = new char[100];
      /* argh how do we fix this */
      link = Link.create_from_track (strack, 0);
      link.as_string (uri);
      stdout.printf ("%s\n", (string) uri);
      track.uri = (string) uri;
      SpotifySource.tracks.append (track);
    }

    search_done = true;

    //search.release ();
    //g_search = NULL;
    //terminate...
  }

  public weak GLib.List<Track> search (string query) {
    search_done = false;

    tracks = new GLib.List<Track> ();

    Search search = Search.create(session, query, 0, 100,
                                  MySearchComplete, null);

    int timeout = -1;
    while (!search_done) {
      session.process_events(&timeout);
      Thread.usleep(100 * timeout);
    }

    return tracks;
  }

  public void set_track (Track track) {
    spotify.set ("spotifyuri", track.uri);
  }

  public Track? create_track_from_uri (string uri) {
    Track tr = new Track();

    Link link = Link.create_from_string (uri);
    if (link == null) {
      /* no spotify link */
      return null;
    }

    Spotify.Track track = link.as_track();
    if (track == null) {
      /* maybe not a track link */
      return null;
    }

    Spotify.Album album = track.album ();
    if (album == null) {
      /* maybe not a track link */
      return null;
    }

    Spotify.Artist artist = track.artist (0);
    if (artist == null) {
      /* maybe not a track link */
      return null;
    }

    tr.name = track.name ();
    tr.uri = uri;
    tr.artist = artist.name ();
    tr.album = album.name ();
    tr.duration = track.duration ().to_string ();

    return tr;
  }

  public string supported_uris () {
    return "spotify";
  }
}
