using Gst;

public interface RemoteSpeaker : GLib.Object, Speaker {
  public abstract string host { get; set; }
}
