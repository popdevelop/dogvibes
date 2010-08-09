/**
 * Using SQLite in Vala Sample Code
 * Port of an example found on the SQLite site.
 * http://www.sqlite.org/quickstart.html
 *
 * sudo apt-get install libsqlite3-dev
 *
 * valac --pkg sqlite3 -o sqlitesample SqliteSample.vala
 * ./sqlitesample test.db "select * from t1 limit 2"
 */

using GLib;
using Sqlite;

public class SqliteSample : GLib.Object {

  private Database db;
  private int ugly_mutex = 0;
  private List<string> tracks = new List<string> ();

  construct {
    int rc;
    string datafile = "dogvibes.db";

    if (!FileUtils.test (datafile, FileTest.IS_REGULAR)) {
      stdout.printf ("Collection: Creating empty database %s\n", datafile);
      rc = Database.open (datafile, out this.db);
      rc = this.db.exec ("create table collection (id INTEGER PRIMARY KEY," +
                         "name TEXT, artist TEXT, album TEXT, k TEXT," +
                         "duration INTEGER)", null, null);
    } else
      rc = Database.open (datafile, out this.db);

    if (rc != Sqlite.OK) {
      stderr.printf ("Can't open database: %d, %s\n", rc, this.db.errmsg ());
      //return 1; // todo: not allowed here...
    }
  }

  private int callback (int n_columns, string[] values,
                              string[] column_names)
  {
    this.tracks.append (values[1]); // todo: create Track objects instead

    /*
    for (int i = 0; i < n_columns; i++) {
      stdout.printf ("%s = %s\n", column_names[i], values[i]);
    }
    stdout.printf ("\n");
    */

    this.ugly_mutex = 0;

    return 0;
  }

  public void add_track (string name, string artist, string album,
                         string key, int duration) {
    string db_query =
      "insert into collection (name, artist, album, k, duration) " +
    "values ('%s', '%s', '%s', '%s', %d)".printf(name, artist, album,
                                                 key, duration);

    stdout.printf ("Collection: Added '%s - %s'\n", artist, name);

    this.db.exec (db_query, null, null);
  }

  public List<string> search (string query) {
    this.ugly_mutex = 1;

    string db_query = "select * from collection where name LIKE '%" + query + "%'";
    this.db.exec (db_query, callback, null);

    while (this.ugly_mutex == 1);

    return this.tracks.copy ();
  }

  public static int main (string[] args) {
    SqliteSample collection = new SqliteSample ();

    collection.add_track ("Johnny", "Memories in Mono", "Pikes & Perches", "file:///mim.ogg", 190);
    collection.add_track ("Marathon", "Memories in Mono", "Pikes & Perches", "file:///Mara_.mp3", 190);
    collection.add_track ("Wonderwall", "Oasis", "Standing...", "file:///oasis.mp3", 190);
    List<string> tracks = collection.search("");

    foreach (string t in tracks) {
      stdout.printf ("... %s\n", t);
    }

    return 0;
  }
}