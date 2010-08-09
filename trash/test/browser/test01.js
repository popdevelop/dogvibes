var t1 = new Tester('one', 'ws://localhost:9999/');
var t2 = new Tester('two', 'ws://localhost:9999/');

initTest();

function run() {
    t1.amp('getQueuePosition');
    t2.amp('getQueuePosition');
    t1.amp('setVolume?level=0.1')
    t1.amp('getQueuePosition');
    t2.amp('getQueuePosition');
    t1.amp('setVolume?level=0.1')
    t1.amp('getQueuePosition');
    t2.amp('getQueuePosition');
    t1.amp('setVolume?level=0.1');

    t2.dogvibes("getAllTracksInPlaylist?playlist_id=999999")
}
