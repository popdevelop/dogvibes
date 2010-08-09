using Gst;

public class FakeSpeaker : GLib.Object, Speaker {
  private Element fakesink;
  private Element queue2;
  private bool created;
  private Bin bin;

  public string name { get; set; }

  public FakeSpeaker (string name) {
    this.name = name;
  }

  construct {
    created = false;
  }

  public weak Bin get_speaker () {
    if (!created) {
      bin = new Bin(name);
      this.fakesink = ElementFactory.make ("fakesink", "fakesink");
      this.queue2 = ElementFactory.make ("queue2", "queue2");
      stdout.printf ("Creating fake sink\n");
      this.fakesink.set ("dump", true);
      bin.add_many (this.queue2, this.fakesink);
      this.queue2.link (this.fakesink);
      GhostPad gpad = new GhostPad ("sink", this.queue2.get_static_pad("sink"));
      bin.add_pad (gpad);
      created = true;
    }
    return bin;
  }
}