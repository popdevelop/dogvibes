using Gst;

public class RadioSource : GLib.Object, Source {
  public static GLib.List<Track> tracks;

  construct {
    stdout.printf ("Creating radio source with\n");
  }

  public weak GLib.List<Track> search (string query) {
    stdout.printf ("I did a search on %s\n", query);
    stdout.printf ("NOT IMPLEMENTED! \n");
    return tracks;
  }

  public Track? create_track_from_uri (string uri) {
    stdout.printf ("create track from uri not implemented\n");
    return null;
  }
}
