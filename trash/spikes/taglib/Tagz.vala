/**
 * apt-get install libtagc0-dev
 * valac --pkg taglib_c -o tagz Tagz.vala
 * ./tagz example.mp3
 */

using GLib;
using TagLib;

public class Tagz : GLib.Object {

  public static int main (string[] args) {
  File f = new File(args[1]);
  unowned Tag t = f.tag;
  unowned string title = t.title;
  unowned string artist = t.artist;
    stdout.printf ("%s - %s\n", artist, title);
    return 0;
  }
}