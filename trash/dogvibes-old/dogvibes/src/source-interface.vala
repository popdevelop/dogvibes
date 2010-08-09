using Gst;

public interface Source : GLib.Object {
  public abstract weak GLib.List<Track> search (string query);
  public abstract Track? create_track_from_uri (string uri);
}
