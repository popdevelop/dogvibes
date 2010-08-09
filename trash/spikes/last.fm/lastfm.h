/*
 * @file lastfm.h
 * @author sebastian.wallin
 * @description public last.fm API 
 */

#ifndef LASTFM_H_
#define LASTFM_H_

#define LFM_URL_MAX_LEN 128
#define LFM_STRING_MAX 128
#define LFM_INT_LEN 12

#define LFM_USER_AGENT "libcurl-agent/1.0"
#define LFM_CLIENT_NAME "tst"
#define LFM_CLIENT_VERS "1.0"

typedef enum LastFM_ResponseCode
{
    LFM_OK,
    LFM_BANNED,
    LFM_BADAUTH,
    LFM_BADSESSION,
    LFM_BADTIME,
    LFM_FAILED
} LastFM_ResponseCode_t;

typedef enum LastFM_SubmissionType
{
    LFM_NOWPLAYING,
    LFM_SUBMIT
} LastFM_SubmissionType_t;

typedef struct LastFM_Session
{
    char sid[33];
    char np_url[LFM_URL_MAX_LEN];
    char sm_url[LFM_URL_MAX_LEN];
} LastFM_Session_t;

typedef struct LastFM_TrackInfo
{
    char artist[LFM_STRING_MAX];
    char track[LFM_STRING_MAX];
    char album[LFM_STRING_MAX];
    char time[LFM_INT_LEN];   /* Timestamp when playing began */
    char length[LFM_INT_LEN]; /* Track length in seconds */
    char tracknumber[LFM_INT_LEN];
    char mb_trackid[37]; /* Optional musicbrainz track ID. 36-bytes UUID */

} LastFM_TrackInfo_t;

/*
 * ----------------- Public API Functions -----------------
 */

LastFM_ResponseCode_t last_fm_submit(
        LastFM_SubmissionType_t type,
        LastFM_TrackInfo_t * track,
        LastFM_Session_t * session);

LastFM_ResponseCode_t last_fm_handshake(
        char * user,
        char * password,
        LastFM_Session_t * session);

#endif /* LASTFM_H_ */
