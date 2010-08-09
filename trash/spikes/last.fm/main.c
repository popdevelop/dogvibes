/*
 * @file main.c
 * @author sebastian.wallin
 * @description Example on how to use the last.fm API
 */
#include <stdio.h>
#include "lastfm.h"

int main(void)
{
    int retval = 1;
    LastFM_Session_t session;
    /* Track info needs to be UTF8-encoded!! */
    LastFM_TrackInfo_t track = {
            "Kalle Jularbo Collective",
            "Sängfösarvals",
            "Dans på bryggan 6, the remixes",
            "1241728779",
            "161",
            "3",
            "\0" };
    if(last_fm_handshake("dogvibes", "password", &session) != LFM_OK)
    {
        puts("Authorization failed!!\n");
        goto done;
    }

    /* We can either submit the track as "now playing" or as a regular submit
     * This is controlled by the first parameter to the submit function.
     * Good or bad idea? dunno yet... */
    if(last_fm_submit(LFM_SUBMIT, &track, &session) != LFM_OK)
    {
        puts("Track submission failed!\n");
        goto done;
    }
    puts("Track successfully submitted!\n");
    retval = 0;
done:
    return retval;
}
