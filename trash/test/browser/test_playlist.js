var t1 = new Tester('one', 'ws://localhost:9999/');

initTest();


function run() {
    // do stuff with non-existing playlist
    t1.sendCmd({ cmd: '/dogvibes/getAllTracksInPlaylist?playlist_id=999999',
                 onReply: function(reply){
                     check(reply.error == 3);
                 }});
    t1.sendCmd({ cmd: '/dogvibes/removeTrackFromPlaylist?playlist_id=999999&track_id=1',
                 onReply: function(reply){
                     check(reply.error == 3);
                 }});
    t1.sendCmd({ cmd: '/dogvibes/removePlaylist?id=999999',
                 onReply: function(reply){
                     check(reply.error == 3);
                 }});
    t1.sendCmd({ cmd: '/dogvibes/addTrackToPlaylist?playlist_id=999999&uri=spotify:track:5WO8Vzz5hFWBGzJaNI5U5n',
                 onReply: function(reply){
                     check(reply.error == 3);
                 }});
    t1.sendCmd({ cmd: '/dogvibes/getAllTracksInPlaylist?playlist_id=999999',
                 onReply: function(reply){
                     check(reply.error == 3);
                 }});

    t1.sendCmd({ cmd: '/dogvibes/createPlaylist?name=playlist_test',
                 onReply: function(reply){
                     check(reply.error == 0);
                 }});

    t1.sendCmd({ cmd: "/dogvibes/getAllPlaylists",
                 onReply: function(reply){
                     check(reply.error == 0);
                     var playlists = reply.result;
                     for (var i = 0; i < playlists.length; ++i) {
                         if ('playlist_test' == playlists[i].name) {
                             playlist_id = playlists[i].id;
                             return
                         }
                     }
                 }});
    t1.sendCmd({ cmd: '/dogvibes/addTrackToPlaylist?uri=spotify:track:0leJr3UNvxrXqrwgE8v0ps', //n&playlist_id=' + playlist_id,
                 onReply: function(reply){
                     check(reply.error == 0);
                 },
                 requires: 'playlist_id'});
    t1.sendCmd({ cmd: "/dogvibes/getAllTracksInPlaylist",
                 onReply: function(reply){
                     check(reply.error == 0);
                     check(reply.result[0].album == 'Human');
                 },
                 requires: 'playlist_id' });

//    t1.sendCmd({ cmd: "/dogvibes/getAllPlaylists",
//                 onReply: function(reply){
//                     var playlists = reply.result;
//                     for (var i = 0; i < playlists.length; ++i) {
//                         playlist_id = playlists[i].id;
//                         t1.sendCmd({ cmd: '/dogvibes/removePlaylist?id=' + playlist_id });
//                     }
//                 }});

//    t1.sendCmd({ cmd: '/dogvibes/addTrackToPlaylist?uri=error_uri&playlist_id=' + playlist_id,
//                 onReply: function(reply){
//                     check(reply.error == 3);
//                 }});
//    t1.sendCmd({ cmd: '/dogvibes/removeTrackFromPlaylist?track_id=999999&playlist_id=' + playlist_id,
//                 onReply: function(reply){
//                     check(reply.error == 3);
//                 }});
//    t1.sendCmd({ cmd: '/dogvibes/createPlaylist',
//                 onReply: function(reply){
//                     check(reply.error == 3);
//                 }});

//    t1.dogvibes("getAllPlaylists");
//    t1.dogvibes("renamePlaylist?playlist_id=16&name=NewName333");
//    t1.dogvibes("getAllPlaylists");
}
