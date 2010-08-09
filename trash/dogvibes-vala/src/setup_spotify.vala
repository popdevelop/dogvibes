using GConf;

public void main (string[] args) {
  try {
    var gc = GConf.Client.get_default ();
    gc.set_string ("/apps/dogvibes/spotify/username", "gyllen");
    gc.set_string ("/apps/dogvibes/spotify/password", "bobidob10");
	} catch (GLib.Error e) {
		stderr.printf ("Oops: %s\n", e.message);
	}
}
