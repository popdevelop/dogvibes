using Gst;

public interface Speaker : GLib.Object {
  public abstract string name { get; set; }
  public abstract weak Bin get_speaker ();
}
