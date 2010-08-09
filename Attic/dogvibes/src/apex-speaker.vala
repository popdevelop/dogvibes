using Gst;

public class ApexSpeaker : GLib.Object, Speaker, RemoteSpeaker {
  private Element apexsink;
  private Bin bin;
  private bool created;
  private Element queue2;

  public string name { get; set; }
  public string host { get; set; }

  public ApexSpeaker (string name, string host) {
    this.name = name;
    this.host = host;
  }

  construct {
    created = false;
  }

  public weak Bin get_speaker () {
    if (!created) {
      bin = new Bin(this.name);
      this.apexsink = ElementFactory.make ("apexsink", "apexsink");
      this.queue2 = ElementFactory.make ("queue2", "queue2");
      this.apexsink.set ("sync", false);
	  this.apexsink.set ("host", this.host);
	  this.apexsink.set ("volume", 100);
      stdout.printf ("Creating apex sink\n");
      bin.add_many (this.queue2, this.apexsink);
      this.queue2.link (this.apexsink);
      GhostPad gpad = new GhostPad ("sink", this.queue2.get_static_pad("sink"));
      bin.add_pad (gpad);
      created = true;
    }
    return bin;
  }
}
