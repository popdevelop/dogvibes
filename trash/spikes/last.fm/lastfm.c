/*
 * @file lastfm.c
 * @author sebastian.wallin
 * @description last.fm API implementation
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "curl/curl.h"
#include "md5.h"
#include "lastfm.h"

/*
 *  --------------- Local defines, structs etc. ---------------
 */


#define LFM_HANDSHAKE_URL "http://post.audioscrobbler.com:80/?hs=true&p=1.2.1&c=%s&v=%s&u=%s&t=%u&a=%s"
//#define LFM_HANDSHAKE_URL "http://localhost:8080/test.php"

#define LFM_NOWPLAYING_FIELDS "s=%s&a=%s&t=%s&b=%s&l=%s&n=%s&m=%s"
#define LFM_SUBMIT_FIELDS "s=%s&a[0]=%s&t[0]=%s&b[0]=%s&l[0]=%s&n[0]=%s&m[0]=%s&i[0]=%s&o[0]=P&r[0]="

//#define DEBUG

struct MemoryStruct
{
    char *memory;
    size_t size;
};


/*
 *  --------------- Local helper functions ---------------
 */

/* Forward declarations */
static void l_hex_bytes_to_string(char* string, unsigned char * hex, int len);
static void l_make_md5_string(char * output, char * input, int len);
static int l_url_escape_track_info(CURL * curl, LastFM_TrackInfo_t * track);
static void *l_myrealloc(void *ptr, size_t size);
static size_t l_write_memory_callback(void *ptr, size_t size, size_t nmemb, void *data);
static LastFM_ResponseCode_t l_last_fm_get_response_code(char * str);

/* Implementations */
static void l_hex_bytes_to_string(char* string, unsigned char * hex, int len)
{
    int i = 0;
    char byte_str[3];
    *string = '\0';
    for (i = 0; i < len; i++)
    {
        sprintf(byte_str, "%02x", hex[i]);
        strcat(string, byte_str);
    }
}

static void l_make_md5_string(char * output, char * input, int len)
{
    struct MD5Context md5c;
    unsigned char temp[16];
    MD5Init(&md5c);
    MD5Update(&md5c, input, len);
    MD5Final(temp, &md5c);
    l_hex_bytes_to_string(output, temp, 16);
}
static int l_url_escape_track_info(CURL * curl, LastFM_TrackInfo_t * track)
{
    /* This is boring... */
    char * temp;
    /* Artist */
    temp = curl_easy_escape(curl, track->artist, 0);
    if(!temp) { return -1; }
    strcpy(track->artist, temp);
    curl_free(temp);

    /* Album */
    temp = curl_easy_escape(curl, track->album, 0);
    if(!temp) { return -1; }
    strcpy(track->album, temp);
    curl_free(temp);

    /* Track name */
    temp = curl_easy_escape(curl, track->track, 0);
    if(!temp) { return -1; }
    strcpy(track->track, temp);
    curl_free(temp);

    return 0;
};



static void *l_myrealloc(void *ptr, size_t size)
{
    /* There might be a realloc() out there that doesn't like reallocing
     NULL pointers, so we take care of it here */
    if (ptr)
        return realloc(ptr, size);
    else
        return malloc(size);
}

static size_t l_write_memory_callback(void *ptr, size_t size, size_t nmemb, void *data)
{
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *) data;

    mem->memory = l_myrealloc(mem->memory, mem->size + realsize + 1);
    if (mem->memory)
    {
        memcpy(&(mem->memory[mem->size]), ptr, realsize);
        mem->size += realsize;
        mem->memory[mem->size] = 0;
    }
    return realsize;
}

static LastFM_ResponseCode_t l_last_fm_get_response_code(char * str)
{
    LastFM_ResponseCode_t retval = LFM_FAILED;
    if(strcmp(str, "OK") == 0)
    {
        retval = LFM_OK;
    }
    else if(strcmp(str, "BANNED") == 0)
    {
        retval = LFM_BANNED;
    }
    else if(strcmp(str, "BADAUTH") == 0)
    {
        retval = LFM_BADAUTH;
    }
    else if(strcmp(str, "BADSESSION") == 0)
    {
        retval = LFM_BADSESSION;
    }
    else if(strcmp(str, "BADTIME") == 0)
    {
        retval = LFM_BADTIME;
    }    
    return retval;
}

/*
 *  --------------- Public API functions ---------------
 */

LastFM_ResponseCode_t last_fm_submit(
        LastFM_SubmissionType_t type,
        LastFM_TrackInfo_t * track,
        LastFM_Session_t * session)
{
    CURLcode ret;
    CURL *curl = curl_easy_init();
    LastFM_ResponseCode_t retval = LFM_FAILED;
    char   submit_fields[0x200]; /* FIXME: dynamic? */
    char * submit_url;
    char * resp_line;
    char * memory_cpy;
    struct MemoryStruct chunk;
    chunk.memory=NULL;
    chunk.size = 0;

    if (curl == NULL)
    {
        fprintf(stderr, "Failed creating CURL easy handle!\n");
        goto done;
    }

    /* URL encode the entire trackinfo */
    if(l_url_escape_track_info(curl, track) != 0)
    {
        goto done;
    }

    /* Fill in common values */


    /* Check submission type. Play now or regular */
    switch(type)
    {
        case LFM_NOWPLAYING:
            submit_url = session->np_url;
            sprintf(submit_fields, LFM_NOWPLAYING_FIELDS,
                    session->sid,
                    track->artist,
                    track->track,
                    track->album,
                    track->length,
                    track->tracknumber,
                    track->mb_trackid);
            break;
        case LFM_SUBMIT:
            submit_url = session->sm_url;
            sprintf(submit_fields, LFM_SUBMIT_FIELDS,
                    session->sid,
                    track->artist,
                    track->track,
                    track->album,
                    track->length,
                    track->tracknumber,
                    track->mb_trackid,
                    track->time);
            break;
        default:
            goto done;
    }

#ifdef DEBUG
    curl_easy_setopt(curl, CURLOPT_VERBOSE, 1);
    printf("Calling: '%s'...\n", submit_url);
#endif

    /* Prepare curl */
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, l_write_memory_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, LFM_USER_AGENT);
    curl_easy_setopt(curl, CURLOPT_POST, 1);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, submit_fields);
    curl_easy_setopt(curl, CURLOPT_URL, submit_url);

    /* Send request */
    ret = curl_easy_perform(curl);
    if (ret != 0)
    {
        fprintf(stderr, "Failed getting %s: %s\n", submit_url,
                curl_easy_strerror(ret));
        goto done;
    }
#ifdef DEBUG
    printf("Got back:\n %s", chunk.memory);
#endif

    /* Check response. Operate on copy of pointer FIXME: necessary? */
    memory_cpy = chunk.memory;
    /* The first line in response should be the response code: parse it!*/
    resp_line = strtok(memory_cpy, "\n\r");
    retval = l_last_fm_get_response_code(resp_line);

done:
    if(chunk.memory != NULL)
    {
        free(chunk.memory);
    }
    return retval;

}

LastFM_ResponseCode_t last_fm_handshake(
        char * user,
        char * password,
        LastFM_Session_t * session)
{
    CURLcode ret;
    CURL *curl = curl_easy_init();
    LastFM_ResponseCode_t retval = LFM_FAILED;
    char hs_url[0x100]; /* FIXME how long?*/
    char token[64];
    char token_md5[33];
    char password_md5[33];

    char * resp_line;
    char * memory_cpy;

    struct MemoryStruct chunk;
    time_t lt = time(NULL);

    /* ... phew, that's alot of crap on stack, let's begin */
    chunk.memory=NULL;
    chunk.size = 0;

    /* Just make sure curl is OK */
    if (curl == NULL)
    {
        fprintf(stderr, "Failed creating CURL easy handle!\n");
        goto done;
    }

    /* first MD5 the password */
    l_make_md5_string(password_md5, password, strlen(password));

    /* concat the timestamp */
    sprintf(token, "%s%u", password_md5, (unsigned int)lt);

    /* MD5 the new string */
    l_make_md5_string(token_md5, token, strlen(token));

    /* Prepare handshake URL */
    sprintf(hs_url, LFM_HANDSHAKE_URL, LFM_CLIENT_NAME, LFM_CLIENT_VERS,
            user,(unsigned int) lt, token_md5);

    /* Prepare curl */
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, l_write_memory_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, LFM_USER_AGENT);
    curl_easy_setopt(curl, CURLOPT_URL, hs_url);

#ifdef DEBUG
    printf("Calling: %s...\n", hs_url);
#endif
    /* Make request */
    ret = curl_easy_perform(curl);
    if (ret != 0)
    {
        fprintf(stderr, "Failed getting %s: %s\n", hs_url,
                curl_easy_strerror(ret));
        goto done;
    }
#ifdef DEBUG
    printf("Got back:\n %s", chunk.memory);
#endif
    /* Operate on copy of pointer */
    memory_cpy = chunk.memory;
    /* The first line in response should be the response code: parse it!*/
    resp_line = strtok(memory_cpy, "\n\r");
    retval = l_last_fm_get_response_code(resp_line);
    if(retval == LFM_OK)
    {
        /* If authorization is ok. Fill in the session*/
        /* First is the session id */
        resp_line = strtok(NULL, "\n\r");
        strcpy(session->sid, resp_line);

        /* Next is the "now playing" url */
        resp_line = strtok(NULL, "\n\r");
        strcpy(session->np_url, resp_line);

        /* Last is the submission url*/
        resp_line = strtok(NULL, "\n\r");
        strcpy(session->sm_url, resp_line);
    }

done:
    if(chunk.memory != NULL)
    {
        free(chunk.memory);
    }
    return retval;

}
