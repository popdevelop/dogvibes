/* libspotify.vapi
 *
 * Copyright (C) 2009  Johan Gyllenspetz
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
 * Authors:
 * 	Johan  Gyllenspetz <johan.gyllenspetz@gmail.com>
 */

namespace LibSpotify
{
/* typedef struct sp_session sp_session; ///< Representation of a session */
/* typedef struct sp_track sp_track; ///< A track handle */
/* typedef struct sp_album sp_album; ///< An album handle */
/* typedef struct sp_artist sp_artist; ///< An artist handle */
/* typedef struct sp_artistbrowse sp_artistbrowse; ///< A handle to an artist browse result */
/* typedef struct sp_albumbrowse sp_albumbrowse; ///< A handle to an album browse result */
/* typedef struct sp_search sp_search; ///< A handle to a search result */
/* typedef struct sp_link sp_link; ///< A handle to the libspotify internal representation of a URI */
/* typedef struct sp_image sp_image; ///< A handle to an image */
/* typedef struct sp_user sp_user; ///< A handle to a user */
/* typedef struct sp_playlist sp_playlist; ///< A playlist handle */
/* typedef struct sp_playlistcontainer sp_playlistcontainer; ///< A playlist container (playlist containing other playlists) handle */
/* typedef enum sp_error { */
/* 	SP_ERROR_OK                        = 0,  ///< No errors encountered */
/* 	SP_ERROR_BAD_API_VERSION           = 1,  ///< The library version targeted does not match the one you claim you support */
/* 	SP_ERROR_API_INITIALIZATION_FAILED = 2,  ///< Initialization of library failed - are cache locations etc. valid? */
/* 	SP_ERROR_TRACK_NOT_PLAYABLE        = 3,  ///< The track specified for playing cannot be played */
/* 	SP_ERROR_RESOURCE_NOT_LOADED       = 4,  ///< One or several of the supplied resources is not yet loaded */
/* 	SP_ERROR_BAD_APPLICATION_KEY       = 5,  ///< The application key is invalid */
/* 	SP_ERROR_BAD_USERNAME_OR_PASSWORD  = 6,  ///< Login failed because of bad username and/or password */
/* 	SP_ERROR_USER_BANNED               = 7,  ///< The specified username is banned */
/* 	SP_ERROR_UNABLE_TO_CONTACT_SERVER  = 8,  ///< Cannot connect to the Spotify backend system */
/* 	SP_ERROR_CLIENT_TOO_OLD            = 9,  ///< Client is too old, library will need to be updated */
/* 	SP_ERROR_OTHER_PERMAMENT           = 10, ///< Some other error occured, and it is permanent (e.g. trying to relogin will not help) */
/* 	SP_ERROR_BAD_USER_AGENT            = 11, ///< The user agent string is invalid or too long */
/* 	SP_ERROR_MISSING_CALLBACK          = 12, ///< No valid callback registered to handle events */
/* 	SP_ERROR_INVALID_INDATA            = 13, ///< Input data was either missing or invalid */
/* 	SP_ERROR_INDEX_OUT_OF_RANGE        = 14, ///< Index out of range */
/* 	SP_ERROR_USER_NEEDS_PREMIUM        = 15, ///< The specified user needs a premium account */
/* 	SP_ERROR_OTHER_TRANSIENT           = 16, ///< A transient error occured. */
/* 	SP_ERROR_IS_LOADING                = 17, ///< The resource is currently loading */
/* } sp_error; */
/* const char* sp_error_message(sp_error error); */
/* typedef enum sp_connectionstate { */
/* 	SP_CONNECTION_STATE_LOGGED_OUT   = 0, ///< User not yet logged in */
/* 	SP_CONNECTION_STATE_LOGGED_IN    = 1, ///< Logged in against a Spotify access point */
/* 	SP_CONNECTION_STATE_DISCONNECTED = 2, ///< Was logged in, but has now been disconnected */
/* 	SP_CONNECTION_STATE_UNDEFINED    = 3, ///< The connection state is undefined */
/* } sp_connectionstate; */

/* typedef enum sp_sampletype { */
/* 	SP_SAMPLETYPE_INT16_NATIVE_ENDIAN = 0, ///< 16-bit signed integer samples */
/* } sp_sampletype; */

/* typedef struct sp_audioformat { */
/* 	sp_sampletype sample_type;   ///< Sample type enum, */
/* 	int sample_rate;             ///< Audio sample rate, in samples per second. */
/* 	int channels;                ///< Number of channels. Currently 1 or 2. */
/* } sp_audioformat; */

/* typedef struct sp_session_callbacks { */
/* 	void *logged_in (sp_session *session, sp_error error); */
/* 	void *logged_out (sp_session *session); */
/* 	void *metadata_updated (sp_session *session); */
/* 	void *connection_error (sp_session *session, sp_error error); */
/* 	void *message_to_user (sp_session *session, const char *message); */
/* 	void *notify_main_thread (sp_session *session); */
/* 	int *music_delivery (sp_session *session, const sp_audioformat *format, const void *frames, int num_frames); */
/* 	void *play_token_lost (sp_session *session); */
/* 	void *log_message (sp_session *session, const char *data); */
/* } sp_session_callbacks; */
/* typedef struct sp_session_config { */
/* 	int api_version;                       ///< The version of the Spotify API your application is compiled with. Set to #SPOTIFY_API_VERSION */
/* 	const char *cache_location;            ///< The location where Spotify will write cache files */
/* 	const char *settings_location;         ///< The location where Spotify will write settings files */
/* 	const void *application_key;           ///< Your application key */
/* 	size_t application_key_size;           ///< The size of the application key in bytes */
/* 	const char *user_agent;                ///< "User-Agent" for your application - max 255 characters long */
/* 	const sp_session_callbacks *callbacks; ///< Delivery callbacks for session events, or NULL if you are not interested in any callbacks (not recommended!) */
/* 	void *userdata;                        ///< User supplied data for your application */
/* } sp_session_config; */
/*     sp_error sp_session_init(const sp_session_config *, sp_session **); */
/* sp_error sp_session_login(sp_session *session, const char *username, const char *password); */
/* sp_user *sp_session_user(sp_session *session); */
/* sp_error sp_session_logout(sp_session *session); */
/* sp_connectionstate sp_session_connectionstate(sp_session *session); */
/* void *sp_session_userdata(sp_session *session); */
/* void sp_session_process_events(sp_session *session, int *next_timeout); */
/* sp_error sp_session_player_load(sp_session *session, sp_track *track); */
/* sp_error sp_session_player_seek(sp_session *session, int offset); */
/* sp_error sp_session_player_play(sp_session *session, bool play); */
/* void sp_session_player_unload(sp_session *session); */
/* sp_playlistcontainer *sp_session_playlistcontainer(sp_session *session); */
/* typedef enum { */
/* 	SP_LINKTYPE_INVALID  = 0, ///< Link type not valid - default until the library has parsed the link, or when parsing failed */
/* 	SP_LINKTYPE_TRACK    = 1, ///< Link type is track */
/* 	SP_LINKTYPE_ALBUM    = 2, ///< Link type is album */
/* 	SP_LINKTYPE_ARTIST   = 3, ///< Link type is artist */
/* 	SP_LINKTYPE_SEARCH   = 4, ///< Link type is search */
/* 	SP_LINKTYPE_PLAYLIST = 5, ///< Link type is playlist */
/* } sp_linktype; */
/* sp_link *sp_link_create_from_string(const char *link); */
/* sp_link *sp_link_create_from_track(sp_track *track, int offset); */
/* sp_link *sp_link_create_from_album(sp_album *album); */
/* sp_link *sp_link_create_from_artist(sp_artist *artist); */
/* sp_link *sp_link_create_from_search(sp_search *search); */
/* sp_link *sp_link_create_from_playlist(sp_playlist *playlist); */
/* int sp_link_as_string(sp_link *link, char *buffer, int buffer_size); */
/* sp_linktype sp_link_type(sp_link *link); */
/* sp_track *sp_link_as_track(sp_link *link); */
/* sp_album *sp_link_as_album(sp_link *link); */
/* sp_artist *sp_link_as_artist(sp_link *link); */
/* void sp_link_add_ref(sp_link *link); */
/* void sp_link_release(sp_link *link); */
/* bool sp_track_is_loaded(sp_track *track); */
/* sp_error sp_track_error(sp_track *track); */
/* int sp_track_num_artists(sp_track *track); */
/* sp_artist *sp_track_artist(sp_track *track, int index); */
/* sp_album *sp_track_album(sp_track *track); */
/* const char *sp_track_name(sp_track *track); */
/* int sp_track_duration(sp_track *track); */
/* int sp_track_popularity(sp_track *track); */
/* int sp_track_disc(sp_track *track); */
/* int sp_track_index(sp_track *track); */
/* void sp_track_add_ref(sp_track *track); */
/* void sp_track_release(sp_track *track); */
/* bool sp_album_is_loaded(sp_album *album); */
/* sp_artist *sp_album_artist(sp_album *album); */
/* const byte *sp_album_cover(sp_album *album); */
/* const char *sp_album_name(sp_album *album); */
/* int sp_album_year(sp_album *album); */
/* void sp_album_add_ref(sp_album *album); */
/* void sp_album_release(sp_album *album); */
/* const char *sp_artist_name(sp_artist *artist); */
/* bool sp_artist_is_loaded(sp_artist *artist); */
/* void sp_artist_add_ref(sp_artist *artist); */
/* void sp_artist_release(sp_artist *artist); */
/* typedef void albumbrowse_complete_cb(sp_albumbrowse *result, void *userdata); */
/* sp_albumbrowse *sp_albumbrowse_create(sp_session *session, sp_album *album, albumbrowse_complete_cb *callback, void *userdata); */
/* bool) sp_albumbrowse_is_loaded(sp_albumbrowse *alb); */
/* sp_error sp_albumbrowse_error(sp_albumbrowse *alb); */
/* sp_album *sp_albumbrowse_album(sp_albumbrowse *alb); */
/* sp_artist *sp_albumbrowse_artist(sp_albumbrowse *alb); */
/* int sp_albumbrowse_num_copyrights(sp_albumbrowse *alb); */
/* const char *sp_albumbrowse_copyright(sp_albumbrowse *alb, int index); */
/* int sp_albumbrowse_num_tracks(sp_albumbrowse *alb); */
/* sp_track *sp_albumbrowse_track(sp_albumbrowse *alb, int index); */
/* const char *sp_albumbrowse_review(sp_albumbrowse *alb); */
/* void sp_albumbrowse_add_ref(sp_albumbrowse *alb); */
/* void sp_albumbrowse_release(sp_albumbrowse *alb); */
/* typedef void artistbrowse_complete_cb(sp_artistbrowse *result, void *userdata); */
/* sp_artistbrowse *sp_artistbrowse_create(sp_session *session, sp_artist *artist, artistbrowse_complete_cb *callback, void *userdata); */
/* bool sp_artistbrowse_is_loaded(sp_artistbrowse *arb); */
/* sp_error sp_artistbrowse_error(sp_artistbrowse *arb); */
/* sp_artist *sp_artistbrowse_artist(sp_artistbrowse *arb); */
/* int sp_artistbrowse_num_portraits(sp_artistbrowse *arb); */
/* const byte *sp_artistbrowse_portrait(sp_artistbrowse *arb, int index); */
/* int sp_artistbrowse_num_tracks(sp_artistbrowse *arb); */
/* sp_track *sp_artistbrowse_track(sp_artistbrowse *arb, int index); */
/* int sp_artistbrowse_num_similar_artists(sp_artistbrowse *arb); */
/* sp_artist *sp_artistbrowse_similar_artist(sp_artistbrowse *arb, int index); */
/* const char *sp_artistbrowse_biography(sp_artistbrowse *arb); */
/* void sp_artistbrowse_add_ref(sp_artistbrowse *arb); */
/* void sp_artistbrowse_release(sp_artistbrowse *arb); */
/* typedef enum { */
/* 	SP_IMAGE_FORMAT_UNKNOWN = -1, ///< Unknown image format */
/* 	SP_IMAGE_FORMAT_RGB   = 0,    ///< 24 bit image in RGB form */
/* 	SP_IMAGE_FORMAT_BGR   = 1,    ///< 24 bit image in BGR form */
/* 	SP_IMAGE_FORMAT_RGBA  = 2,    ///< 32 bit image in RGBA form */
/* 	SP_IMAGE_FORMAT_RGBA_PRE= 3,  ///< 32 bit image in RGBA form with premultiplied alpha channel */
/* 	SP_IMAGE_FORMAT_BGRA  = 4,    ///< 32 bit image in BGRA form */
/* 	SP_IMAGE_FORMAT_BGRA_PRE= 5,  ///< 32 bit image in BGRA form with premultiplied alpha channel */
/* } sp_imageformat; */
/* typedef void image_loaded_cb(sp_image *image, void *userdata); */
/* sp_image * sp_image_create(sp_session *session, const byte image_id[20]); */
/* void sp_image_add_load_callback(sp_image *image, image_loaded_cb *callback, void *userdata); */
/* void sp_image_remove_load_callback(sp_image *image, image_loaded_cb *callback, void *userdata); */
/* bool sp_image_is_loaded(sp_image *image); */
/* sp_error sp_image_error(sp_image *image); */
/* int sp_image_width(sp_image *image); */
/* int sp_image_height(sp_image *image); */
/* sp_imageformat sp_image_format(sp_image *image); */
/* void *sp_image_lock_pixels(sp_image *image, int *pitch); */
/* void sp_image_unlock_pixels(sp_image *image); */
/* const byte *sp_image_image_id(sp_image *image); */
/* void sp_image_add_ref(sp_image *image); */
/* void sp_image_release(sp_image *image); */
/* typedef void search_complete_cb(sp_search *result, void *userdata); */
/* sp_search *sp_search_create(sp_session *session, const char *query, int offset, int count, search_complete_cb *callback, void *userdata); */
/* bool sp_search_is_loaded(sp_search *search); */
/* sp_error sp_search_error(sp_search *search); */
/* int sp_search_num_tracks(sp_search *search); */
/* sp_track *sp_search_track(sp_search *search, int index); */
/* int sp_search_num_albums(sp_search *search); */
/* sp_album *sp_search_album(sp_search *search, int index); */
/* int sp_search_num_artists(sp_search *search); */
/* sp_artist *sp_search_artist(sp_search *search, int index); */
/* const char *sp_search_query(sp_search *search); */
/* const char *sp_search_did_you_mean(sp_search *search); */
/* int sp_search_total_tracks(sp_search *search); */
/* void sp_search_add_ref(sp_search *search); */
/* void sp_search_release(sp_search *search); */

/* typedef struct sp_playlist_callbacks { */
/* 	void *tracks_added (sp_playlist *pl, const sp_track **tracks, int num_tracks, int position, void *userdata); */
/* 	void *tracks_removed (sp_playlist *pl, const int *tracks, int num_tracks, void *userdata); */
/* 	void *tracks_moved (sp_playlist *pl, const int *tracks, int num_tracks, int new_position, void *userdata); */
/* 	void *playlist_renamed (sp_playlist *pl, void *userdata); */
/* 	void *playlist_state_changed (sp_playlist *pl, void *userdata); */
/* 	void *playlist_update_in_progress (sp_playlist *pl, bool done, void *userdata); */
/* } sp_playlist_callbacks; */

/* bool sp_playlist_is_loaded(sp_playlist *playlist); */
/* void sp_playlist_add_callbacks(sp_playlist *playlist, sp_playlist_callbacks *callbacks, void *userdata); */
/* void sp_playlist_remove_callbacks(sp_playlist *playlist, sp_playlist_callbacks *callbacks, void *userdata); */
/* int sp_playlist_num_tracks(sp_playlist *playlist); */
/* sp_track *sp_playlist_track(sp_playlist *playlist, int index); */
/* const char *sp_playlist_name(sp_playlist *playlist); */
/* sp_error sp_playlist_rename(sp_playlist *playlist, const char *new_name); */
/* sp_user *sp_playlist_owner(sp_playlist *playlist); */
/* bool sp_playlist_is_collaborative(sp_playlist *playlist); */
/* void sp_playlist_set_collaborative(sp_playlist *playlist, bool collaborative); */
/* bool sp_playlist_has_pending_changes(sp_playlist *playlist); */
/* sp_error sp_playlist_add_tracks(sp_playlist *playlist, const sp_track **tracks, int num_tracks, int position); */
/* sp_error sp_playlist_remove_tracks(sp_playlist *playlist, const int *tracks, int num_tracks); */
/* sp_error sp_playlist_reorder_tracks(sp_playlist *playlist, const int *tracks, int num_tracks, int new_position); */

/* typedef struct sp_playlistcontainer_callbacks { */
/* 	void *playlist_added (sp_playlistcontainer *pc, sp_playlist *playlist, int position, void *userdata); */

/* 	void *playlist_removed (sp_playlistcontainer *pc, sp_playlist *playlist, int position, void *userdata); */
/* 	void *playlist_moved (sp_playlistcontainer *pc, sp_playlist *playlist, int position, int new_position, void *userdata); */
/* } sp_playlistcontainer_callbacks; */
/* void sp_playlistcontainer_add_callbacks(sp_playlistcontainer *pc, sp_playlistcontainer_callbacks *callbacks, void *userdata); */
/* void sp_playlistcontainer_remove_callbacks(sp_playlistcontainer *pc, sp_playlistcontainer_callbacks *callbacks, void *userdata); */
/* int sp_playlistcontainer_num_playlists(sp_playlistcontainer *pc); */
/* sp_playlist *sp_playlistcontainer_playlist(sp_playlistcontainer *pc, int index); */
/* sp_playlist *sp_playlistcontainer_add_new_playlist(sp_playlistcontainer *pc, const char *name); */
/* sp_playlist *sp_playlistcontainer_add_playlist(sp_playlistcontainer *pc, sp_link *link); */
/* sp_error sp_playlistcontainer_remove_playlist(sp_playlistcontainer *pc, int index); */
/* sp_error sp_playlistcontainer_move_playlist(sp_playlistcontainer *pc, int index, int new_position); */
/* const char *sp_user_canonical_name(sp_user *user); */
/* const char *sp_user_display_name(sp_user *user); */
/* bool sp_user_is_loaded(sp_user *user); */
}
