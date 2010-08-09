
using Gst;
using GConf;

[DBus (name = "com.Dogvibes.Dogvibes")]
public class Dogvibes : GLib.Object {
  /* list of all sources */
  public static GLib.List<Source> sources;

  /* list of all speakers */
  public static GLib.List<Speaker> speakers;

  construct {
    /* create lists of speakers and sources */
    sources = new GLib.List<Source> ();
    speakers = new GLib.List<Speaker> ();

    /* initiate all sources */
    /* initiate one spotify source (this should all be done from conffiles according to last state */
    sources.append (new SpotifySource ("gyllen", "bobidob10"));

    /* initiate one file source */
    sources.append (new FileSource ("/home/johan/Desktop/mp3"));

    /* initiate one radio source */
    sources.append (new RadioSource ());

    /* initiate all speakers */
    speakers.append (new DeviceSpeaker ("devicesource"));
    speakers.append (new FakeSpeaker ("fakesource"));
    speakers.append (new ApexSpeaker ("apexsource", "192.168.1.3"));
  }

  /*** public D-Bus API ***/

  public HashTable<string,string>[] search (string query) {
    GLib.List<Track> tracks = new GLib.List<Track> ();

    foreach (Source source in sources) {
      foreach (Track track in source.search (query)) {
        /* tried to do this with concat but I ended up in an eternal loop... */
        tracks.append(track);
      }
    }

    HashTable<string,string>[] ret = new HashTable<string,string>[tracks.length ()];
    int i = 0;
    foreach (Track track in tracks) {
      ret[i] = track.to_hash_table ();
      i++;
    }

    return ret;
  }

  /*** static methods ***/

  public static weak GLib.List<Source> get_sources () {
    return sources;
  }

  public static weak GLib.List<Speaker> get_speakers () {
    return speakers;
  }

  public static Track? create_track_from_uri (string uri) {
    Track track = null;
    /* we should probably attach tracks here and return a list of matching tracks */
    foreach (Source source in sources) {
      stdout.printf ("Beffo\n");
      track = source.create_track_from_uri (uri);
      stdout.printf ("Affo\n");
      if (track != null) {
        break;
      }
    }
    return track;
  }
}

[DBus (name = "com.Dogvibes.Amp")]
public class Amp : GLib.Object {
  /* the amp pipeline */
  private Pipeline pipeline = null;

  /* the amp pipline bus */
  private Bus bus = null;

  /* sources */
  private weak Source source;

  /* speakers */
  private weak Speaker speaker;

  /* elements */
  private Element src = null;
  private weak Element sink = null;
  private Element tee = null;
  private Element decodebin = null;
  private Element spotify = null;
  private Element volume = null;

  /* playqueue */
  GLib.List<Track> playqueue;

  /* FIXME: stupid to have this as a int it should be a list element instead */
  int playqueue_position;

  /* ugly hack waiting for mr fuck up */
  private bool spotify_in_use;

  weak GLib.List<Source> sources;
  weak GLib.List<Speaker> speakers;

  construct {
    sources = Dogvibes.get_sources ();
    speakers = Dogvibes.get_speakers ();

    source = sources.nth_data (0);
    spotify = ((SingleSource) source).get_src ();

    /* initiate the pipeline */
    pipeline = (Pipeline) new Pipeline ("dogvibes");

    /* create volume element */
    volume = ElementFactory.make ("volume", "volume");
    pipeline.add (volume);

    /* create the tee */
    tee = ElementFactory.make ("tee", "tee");
    pipeline.add (tee);

    /* link volume with tee */
    volume.link (tee);

    /* get pipline bus */
    bus = pipeline.get_bus ();
    bus.add_signal_watch ();
    bus.message += pipeline_eos;

    /* initiate play queue */
    playqueue = new GLib.List<Track> ();
    playqueue_position = 0;
  }

  /*** public D-Bus API ***/

  public void connect_speaker (int nbr) {
    if (!speaker_exists (nbr)) {
      stdout.printf ("Speaker %d does not exist\n", nbr);
      return;
    }

    speaker = speakers.nth_data (nbr);

    if (pipeline.get_by_name (speaker.name) == null) {
      State state;
      State pending;
      pipeline.get_state (out state, out pending, 0);
      pipeline.set_state (State.NULL);
      sink = speaker.get_speaker ();
      pipeline.add (sink);
      tee.link (sink);
      pipeline.set_state (state);
    } else {
      stdout.printf ("Speaker already connected\n");
    }
  }

  public void disconnect_speaker (int nbr) {
    if (!speaker_exists (nbr)) {
      stdout.printf ("Speaker %d does not exist\n", nbr);
      return;
    }

    speaker = speakers.nth_data (nbr);

    if (pipeline.get_by_name (speaker.name) != null) {
      State state;
      State pending;
      pipeline.get_state (out state, out pending, 0);
      pipeline.set_state (State.NULL);
      Element rm = pipeline.get_by_name (speaker.name);
      pipeline.remove (rm);
      tee.unlink (rm);
      pipeline.set_state (state);
    } else {
      stdout.printf ("Speaker not connected\n");
    }
  }

  public HashTable<string,string>[] get_all_tracks_in_queue () {
    int i = 0;
    HashTable<string,string>[] ret = new HashTable<string,string>[playqueue.length ()];
    foreach (Track item in playqueue) {
      ret[i] = item.to_hash_table();
      i++;
    }
    return ret;
  }

  public void get_connected_source () {
	  stdout.printf("NOT IMPLEMENTED \n");
  }

  public void get_connected_speakers () {
	  stdout.printf("NOT IMPLEMENTED \n");
  }

  public void get_available_speakers () {
	  stdout.printf("NOT IMPLEMENTED \n");
  }

  public int get_played_seconds () {
    int64 duration;
    Format for = Format.TIME;
    pipeline.query_position (ref for, out duration);
    duration = duration / MSECOND;
    return (int) duration;
  }

  public int get_queue_position () {
    return playqueue_position;
  }

  public HashTable<string,string> get_status () {
    State state;
    Track track;
    State pending;

    HashTable<string,string> hashtable = new HashTable<string,string>(str_hash, str_equal);

    if (playqueue.length () == 0) {
      return hashtable;
    }

    /* add loaded track information */
    track = (Track) playqueue.nth_data (playqueue_position);
    hashtable.insert ("title", track.name);
    hashtable.insert ("artist", track.artist);
    hashtable.insert ("album", track.album);
    hashtable.insert ("duration", track.duration);
    hashtable.insert ("uri", track.uri);

    /* add state status */
    pipeline.get_state (out state, out pending, 0);
    if (state == State.PLAYING) {
      hashtable.insert ("state", "playing");
    } else if (state == State.NULL) {
      hashtable.insert ("state", "stopped");
    } else {
      hashtable.insert ("state", "paused");
    }

    /* add playqueue status */
    hashtable.insert ("playqueuehash", get_hash_from_playqueue ());

    return hashtable;
  }

  public void next_track () {
    change_track (playqueue_position + 1);
  }

  public void pause () {
    pipeline.set_state (State.PAUSED);
  }

  public void play () {
    Track track;
    track = (Track) playqueue.nth_data (playqueue_position);
    play_only_if_null (track);
  }

  public void play_track (int tracknbr) {
    change_track (tracknbr);
    play ();
  }

  public void previous_track () {
    change_track (playqueue_position - 1);
  }

  public void remove_from_queue (int nbr) {
    if (nbr > (playqueue.length () - 1)) {
      stdout.printf ("Too high track number, %d does not exist in queue\n", nbr);
    }
    playqueue.remove (playqueue.nth_data (nbr));

    /* if current track is removed do nothing */
    if (nbr <= playqueue_position) {
      playqueue_position = playqueue_position - 1;
    }
  }

  public void queue (string uri) {
    Track track = Dogvibes.create_track_from_uri (uri);
    if (track != null) {
      playqueue.append (track);
    }
  }

  public void resume () {
    pipeline.set_state (State.PLAYING);
  }

  public void seek (int msecond) {
    pipeline.seek_simple (Format.TIME, SeekFlags.NONE, ((int64) msecond) * MSECOND);
  }

  public void stop () {
    pipeline.set_state (State.NULL);
  }

  public void set_volume (double vol) {
    if (vol > 1 || vol < 0) {
      stdout.printf ("Volume must be between 0.0 and 1.0\n");
      return;
    }
    volume.set ("volume", (double) vol);
  }

  /*** state change functions ***/

  private void pad_added (Element dec, Pad pad) {
    stdout.printf ("Found suitable plugins lets add the speaker\n");
    /* FIXME the speaker and the tee should not be added to the pipeline here */
    pad.link (volume.get_pad("sink"));
    volume.set_state (State.PAUSED);
    tee.set_state (State.PAUSED);
  }

  /*** private helper functions ***/

  private void change_track (int tracknbr) {
    State pending;
    State state;
    Track track;

    if (tracknbr > (playqueue.length () - 1)) {
      stdout.printf ("Track number %d is to larges play queue is %u long\n", tracknbr, playqueue.length ());
      return;
    }

    if (tracknbr == playqueue_position) {
      /* do nothing we are at the correct position */
      return;
    }

    if (tracknbr < 0) {
      tracknbr = 0;
    }

    playqueue_position = tracknbr;
    track = (Track) playqueue.nth_data (playqueue_position);

    pipeline.get_state (out state, out pending, 0);
    pipeline.set_state (State.NULL);
    play_only_if_null (track);
    pipeline.set_state (state);
  }

  private string get_hash_from_playqueue () {
    string tohash = new string();
    foreach (Track item in playqueue) {
      tohash += item.uri;
    }
    return Checksum.compute_for_string (ChecksumType.MD5, tohash);
  }

  private void pipeline_eos (Gst.Bus bus, Gst.Message mes) {
    if (mes.type == Gst.MessageType.EOS) {
      next_track ();
    }
  }

  private void play_only_if_null (Track? track) {
    State state;
    State pending;
    pipeline.get_state (out state, out pending, 0);

    if (state != State.NULL || track == null) {
      pipeline.set_state (State.PLAYING);
      return;
    }

    /* waiting for mr fuckup to complete his task */
    if (src != null) {
      pipeline.remove (src);
      if (!spotify_in_use) {
        stdout.printf("Removed a decodebin\n");
        pipeline.remove (decodebin);
      }
    }

    /* waiting for mr fuckup to complete his task */
    if (track.uri.substring (0,7) == "spotify") {
      src = spotify;
      ((SingleSource) source).set_track (track);
      pipeline.add (spotify);
      spotify.link (volume);
      spotify_in_use = true;
    } else {
      src = Element.make_from_uri (URIType.SRC, track.uri , "source");
      decodebin = ElementFactory.make ("decodebin2" , "decodebin2");
      decodebin.pad_added += pad_added;
      pipeline.add_many (src, decodebin);
      src.link (decodebin);
      spotify_in_use = false;
    }
    pipeline.set_state (State.PLAYING);
  }

  private bool speaker_exists (int nbr) {
    if (nbr > (speakers.length () - 1)) {
      stdout.printf ("Speaker %d does not exist\n", nbr);
      return false;
    } else {
      return true;
    }
  }
}

public void main (string[] args) {
  var loop = new MainLoop (null, false);
  Gst.init (ref args);

  try {
    /* register DBus session */
    var conn = DBus.Bus.get (DBus.BusType. SYSTEM);
    dynamic DBus.Object bus = conn.get_object ("org.freedesktop.DBus",
                                               "/org/freedesktop/DBus",
                                               "org.freedesktop.DBus");
    uint request_name_result = bus.request_name ("com.Dogvibes", (uint) 0);

    if (request_name_result == DBus.RequestNameReply.PRIMARY_OWNER) {
      /* register dogvibes server */
      var dogvibes = new Dogvibes ();
      conn.register_object ("/com/dogvibes/dogvibes", dogvibes);

      /* register amplifier */
      var amp = new Amp ();
      conn.register_object ("/com/dogvibes/amp/0", amp);
      amp.connect_speaker (0);
      loop.run ();
    }
  } catch (GLib.Error e) {
    stderr.printf ("Oops: %s\n", e.message);
  }
}
