using Gst;

public class FileSource : GLib.Object, Source {
  private string dir;
  private Collection collection = new Collection ();

  public FileSource (string dir) {
    stdout.printf("Creating file source\n");

    this.dir = dir;
    collection.index(this.dir);
  }

  public weak GLib.List<Track> search (string query) {
    return collection.search (query);
  }

  public Track? create_track_from_uri (string uri) {
    return collection.create_track_from_uri (uri);
  }
}