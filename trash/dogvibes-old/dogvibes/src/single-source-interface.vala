using Gst;

public interface SingleSource : Source, GLib.Object {
  public abstract weak Amplifier owner { get; set; }

  public abstract Bin get_src ();
  public abstract void set_track (Track track);
  public abstract string supported_uris ();
}
