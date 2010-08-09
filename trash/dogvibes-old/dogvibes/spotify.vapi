/* spotify.vapi
 *
 * Copyright (C) 2009 Johan Brissmyr
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.

 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.

 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
 *
 * Author:
 *  Johan Brissmyr <brissmyr@dogvibes.com>
 */

/*
 * TODO: go through and mark out, weak etc.
 */

[CCode (lower_case_cprefix = "", cheader_filename = "spotify/api.h")]
namespace Spotify {

  public const int SPOTIFY_API_VERSION;

  [CCode (cname = "sp_error", cprefix = "SP_ERROR_")]
  public enum Error {
    OK, BAD_API_VERSION, API_INITIALIZATION_FAILED, TRACK_NOT_PLAYABLE,
    RESOURCE_NOT_LOADED, BAD_APPLICATION_KEY, BAD_USERNAME_OR_PASSWORD,
    USER_BANNED, UNABLE_TO_CONTACT_SERVER, CLIENT_TOO_OLD, OTHER_PERMAMENT,
    BAD_USER_AGENT, MISSING_CALLBACK, INVALID_INDATA, INDEX_OUT_OF_RANGE,
    USER_NEEDS_PREMIUM, OTHER_TRANSIENT, IS_LOADING
  }

  [CCode (cname = "sp_sampletype", cprefix = "SP_SAMPLETYPE_")]
  public enum SampleType {
    INT16_NATIVE_ENDIAN
  }

  [CCode (cname = "sp_error_message")]
  public string message (Error error); // weak?

  public static delegate void LoggedIn (Session session, Error error);
  public static delegate void LoggedOut (Session session);
  public static delegate void MetadataUpdated (Session session);
  public static delegate void ConnectionError (Session session, Error error);
  public static delegate void MessageToUser (Session session, string message);
  public static delegate void NotifyMainThread (Session session);
  //public static delegate int MusicDelivery (Session session, AudioFormat format, const void *frames, int num_frames); // use Frame[]
  public static delegate void PlayTokenLost (Session session);
  public static delegate void LogMessage (Session session, string data);

  [CCode (cname = "sp_session_callbacks", destroy_function = "")]
  public struct SessionCallbacks {
    public LoggedIn logged_in;
    public LoggedOut logged_out;
    public MetadataUpdated metadata_updated;
    public ConnectionError connection_error;
    public MessageToUser message_to_user;
    public NotifyMainThread notify_main_thread;
    //public MusicDelivery music_delivery;
    public PlayTokenLost play_token_lost;
    public LogMessage log_message;
  }

  [CCode (cname = "sp_session_config", destroy_function = "")]
  public struct SessionConfig {
    public int api_version;
    public string cache_location;
    public string settings_location;
    [CCode (array_length = false)]
    public uint8[] application_key;
    public int application_key_size;
    public string user_agent;
    public SessionCallbacks *callbacks;
    [CCode (cname = "sp_session_init")]
    public Error init_session (Session *session);
  }

  [CCode (cname = "sp_audioformat", destroy_function = "")]
  public struct AudioFormat {
    public weak SampleType sample_type;
    public int sample_rate;
    public int channels;
  }

  [CCode (cname = "sp_session", cprefix = "sp_session_", unref_function = "")]
  public class Session {
    public weak Error login (string username, string password);
    public weak User user ();
    public weak Error logout ();
    public void process_events (int *next_timeout);
  }

  [CCode (cname = "sp_user", cprefix = "sp_user_", ref_function = "",
          unref_function = "")]
  public class User {
    public weak string canonical_name ();
    public weak string display_name ();
    public bool is_loaded ();
  }

  [CCode (cname = "search_complete_cb")]
  public static delegate void SearchComplete (Search result, void *userdata);

  [CCode (cname = "sp_search", cprefix = "sp_search_", ref_function = "",
          unref_function = "")]
  public class Search {
    public static weak Search create (Session session, string query, int offset,
                                      int count, SearchComplete callback,
                                      void *userdata); // todo: constructor ?
    public void release ();
    public weak Error error ();
    public weak string query ();
    public weak string did_you_mean ();
    public int total_tracks ();
    public int num_tracks ();
    public weak Track track (int index);
    public int num_artists ();
    public weak Artist artist (int index);
    public int num_albums ();
    public weak Album album (int index);
  }

  [CCode (cname = "sp_track", cprefix = "sp_track_", ref_function = "sp_track_add_ref",
          ref_function_void = true, unref_function = "sp_track_release")]
  public class Track {
    public weak string name ();
    public int num_artists ();
    public weak Artist? artist (int index);
    public weak Album? album ();
    public int duration ();
    public int popularity ();
  }

  [CCode (cname = "sp_album", cprefix = "sp_album_", ref_function = "sp_album_add_ref",
          ref_function_void = true, unref_function = "sp_album_release")]
  public class Album {
    public weak string name ();
    public int year ();
  }

  [CCode (cname = "sp_artist", cprefix = "sp_artist_", ref_function = "sp_artist_add_ref",
          ref_function_void = true, unref_function = "sp_artist_release")]
  public class Artist {
    public weak string name ();
  }

  [CCode (cname = "sp_link", cprefix = "sp_link_", ref_function = "sp_link_add_ref",
          ref_function_void = true, unref_function = "sp_link_release")]
  public class Link {
    public static Link? create_from_track (Track track, int offset);
    public static Link? create_from_string (string uri);
    public weak Track? as_track ();
    public weak Album? as_album ();
    public weak Artist? as_artist ();
    public int as_string (char[] buf);
  }
}
