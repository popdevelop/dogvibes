/*
 * Compile: valac --pkg gio-2.0 Indexer.vala -o indexer
 */

using GLib;

public class Indexer : GLib.Object {

  private static void parse_dir (string path) {

    File file = File.new_for_path (path);

    if (!file.query_exists (null)) {
      stderr.printf ("File '%s' doesn't exist.\n", file.get_path ());
      return;
    }

    if (file.query_file_type (0, null) != FileType.DIRECTORY) {
      return;
    }

    try {
      string attributes = FILE_ATTRIBUTE_STANDARD_NAME + "," +
                          FILE_ATTRIBUTE_STANDARD_TYPE;

      FileEnumerator iter = file.enumerate_children (attributes,
                                                     FileQueryInfoFlags.NONE,
                                                     null);
      FileInfo info = iter.next_file (null);

      while (info != null) {
        string full_path = file.get_path () + "/" + info.get_name ();

        if (info.get_file_type () == FileType.DIRECTORY) {
          parse_dir (full_path);
        } else {
          if (full_path.substring (-4, -1) == ".mp3")
          stdout.printf ("Adding %s to library\n", full_path);
        }

        info = iter.next_file (null);
      }

    } catch (IOError e) {
      error ("%s", e.message);
    }

  }

  public static int main (string[] args) {
    Indexer.parse_dir (args[1]);
    return 0;
  }
}
