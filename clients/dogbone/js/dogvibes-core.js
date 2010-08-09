
/*************************************
 * Dogvibes server API
 * Requires jQuery and jsonp plugin
 *************************************/


/* AJAX and websocket connection objects. A connection object is expected
 * to have the following members:
 * - status            : JS object with current server status
 * - start(server)     : function to start the connection to server
 * - stop              :
 * - send(URL, Success): function to send a command to the server
 *
 * Connection object is also expected to trigger the following events:
 * - "Server.connected": upon successful connection
 * - "Server.status"   : when server has new status
 * - "Server.error"    : when server error occurred (disconnected)
 */

/* Polling AJAX connection type */
var AJAX = {
  server: "",
  status: Array(),
  connected: false,
  interval: 500,
  request: false,
  timer: false,

  /* reconnection params */
  delay: 2000,
  attempts: 4,

  start: function(server, user) {
    AJAX.server = server + "/" + user;
    AJAX.timer = setTimeout(AJAX.getStatus, 0);
    return true;
  },
  stop: function() {
    AJAX.connected = false;
    AJAX.request.abort();
    clearTimeout(AJAX.timer);
    AJAX.status = Dogvibes.defaultStatus;
    $(document).trigger("Server.status");
  },
  error: function() {
    /* Try to reconnect before giving up */
    AJAX.connected = false;
    clearTimeout(AJAX.timer);
    if(AJAX.attempts-- > 0) {
      /* Wait longer and longer */
      AJAX.timer = setTimeout(AJAX.getStatus, AJAX.delay *= 2);
      return;
    }
    /* Give up */
    $(document).trigger("Server.error");
    AJAX.stop();
  },
  send: function(URL, Success, Context) {
    /* Changing state? */
    if(!AJAX.connected) {
      $(document).trigger("Server.connecting");
    }
    
    var opts = {
      url: AJAX.server + URL,
      error: AJAX.error,
      success: eval(Success),
      callbackParameter: "callback",
      timeout: 5000
    };
    if(typeof(Context) != "undefined") {
      opts.context = Context;
    }
    AJAX.request = $.jsonp(opts);
  },
  /* Private functions */
  getStatus: function() {
    /* TODO: avoid forward reference */
    clearTimeout(AJAX.timer);
    AJAX.send(Dogvibes.defAmp + Dogvibes.cmd.status, "AJAX.handleStatus");
  },
  handleStatus: function(data) {
    /* Changing state? */
    if(!AJAX.connected) {
      AJAX.connected = true;
      /* Reset */
      AJAX.attempts = 4;
      AJAX.delay = 2000;
      $(document).trigger("Server.connected");
    }
    clearTimeout(AJAX.timer);
    AJAX.timer = setTimeout(AJAX.getStatus, AJAX.interval);

    AJAX.status = data;
    $(document).trigger("Server.status");
  }
};


/* TODO: Websockets connection type */
var WSocket = {
  status: {},
  ws: false,
  connected: false,
  attempts: 300,
  delay: 2000,
  timer: false,
  server: false,
  user: false,
  start: function(server, user) {
    if("WebSocket" in window) {
      $(document).trigger("Server.connecting");
      /* Start reconnection procedure after timeout */
      WSocket.timer = setTimeout(WSocket.error, WSocket.delay*3);
      WSocket.ws = new WebSocket(server + "/stream/" + user);
      WSocket.server = server;
      WSocket.user = user;
      WSocket.ws.onopen = function() {
        clearTimeout(WSocket.timer);
        WSocket.connected = true;
        WSocket.getStatus();
        WSocket.attempts = 300;
        WSocket.delay = 2000;
        $(document).trigger("Server.connected");
      };
      WSocket.ws.onmessage = function(e){ eval(e.data); };
      WSocket.ws.onclose = WSocket.error;
      WSocket.ws.onerror = WSocket.error;
      return true;
    }
    return false;
  },
  stop: function() {
    WSocket.connected = false;
    WSocket.status = Dogvibes.defaultStatus;
    $(document).trigger("Server.error");
    $(document).trigger("Server.status");
  },
  error: function() {
    WSocket.status = Dogvibes.defaultStatus;
    $(document).trigger("Server.status");
    clearTimeout(WSocket.timer)
    if(WSocket.attempts-- > 0) {
      WSocket.timer = setTimeout(function() {
        WSocket.start(WSocket.server, WSocket.user);
      }, WSocket.delay);
    }
    /* Give up */
    WSocket.stop();
  },
  send: function(URL, Success, Context) {
    Success = typeof(Success) == "undefined" ? "WSocket.getStatus" : Success;
    try {
      if (URL.indexOf('?') == -1) {
        WSocket.ws.send(URL + "?callback="+Success);
      } else {
        WSocket.ws.send(URL + "&callback="+Success);
      }
    }
    catch (e){

    }
  },
  getStatus: function() {
    WSocket.send(Dogvibes.defAmp + Dogvibes.cmd.status, "WSocket.handleStatus");
  },
  /* Private functions */
  handleStatus: function(json) {
    WSocket.status = json;
    $(document).trigger("Server.status");

  }
};
/* Workaround for server hard coded callback */
var pushHandler = WSocket.handleStatus;

/********************************
 * Dogvibes server API functions
 ********************************/
window.Dogvibes =  {
  server: false,
  serverURL: false,
  dogtag: "anonymous",
  status: {},
  defAmp: "/amp/0" , /* TODO: dynamic */
  /* Translation table protocol -> connection object */
  protHandlers: {
    ws: WSocket,
    http: AJAX
  },
  cmd: {
    status: "/getStatus",
    prev:   "/previousTrack",
    play:   "/play",
    playTrack: "/playTrack?nbr=",
    queue:  "/queue?uri=",
    queueAlbum: "/queueAlbum?uri=",
    queueAndPlay: "/queueAndPlay?uri=",
    removeTrack : "/removeTrack?track_id=",
    removeTracks: "/removeTracks?track_ids=",
    pause:  "/pause",
    next:   "/nextTrack",
    seek:   "/seek?mseconds=",
    volume: "/setVolume?level=",
    albumArt: "/dogvibes/getAlbumArt?album=",
    moveInPlaylist: "/dogvibes/moveTrackInPlaylist?playlist_id=",
    playlists: "/dogvibes/getAllPlaylists",
    playlist: "/dogvibes/getAllTracksInPlaylist?playlist_id=",
    addtoplaylist: "/dogvibes/addTrackToPlaylist?playlist_id=",
    addAlbumToPlaylist: "/dogvibes/addAlbumToPlaylist?playlist_id=",
    removeFromPlaylist: "/dogvibes/removeTrackFromPlaylist?track_id=",
    removeTracksFromPlaylist: "/dogvibes/removeTracksFromPlaylist?track_ids=",
    createPlaylist: "/dogvibes/createPlaylist?name=",
    removePlaylist: "/dogvibes/removePlaylist?id=",
    renamePlaylist: "/dogvibes/renamePlaylist?playlist_id=",
    playqueue: "/getAllTracksInQueue",
    search: "/dogvibes/search?query=",
    setVolume: "/setVolume?level=",
    getAlbums: "/dogvibes/getAlbums?query=",
    getAlbum: "/dogvibes/getAlbum?album_uri=",
    getPlayedMilliSecs: "/dogvibes/getPlayedMilliSeconds",
    vote: "/addVote?user=",
    getActivity: "/getActivity"
  },
  /*****************
   * Initialization
   *****************/
  init: function(protocol, server, user) {
    $(document).bind("Server.status", Dogvibes.handleStatus);
//    Dogvibes.server = protocol == 'ws' ? WSocket : AJAX;
    Dogvibes.albumartURL = "http://" + server + "/" + user;

    /* Try all protocols */
    for(var prot in protocol) {
      prot = protocol[prot];
      var tempServer = prot + "://" + server;
      if(prot in Dogvibes.protHandlers &&
         Dogvibes.protHandlers[prot].start(tempServer, user)) {
        /* Protocol available and working, settle for it */
        Dogvibes.server = Dogvibes.protHandlers[prot];
        Dogvibes.serverURL = tempServer;
        break;
      }
    }
  },
  /* Handle new status event from connection object and dispatch events */
  handleStatus: function() {
    var data = Dogvibes.server.status;
    if(typeof(data.error) != 'undefined' && data.error !== 0) {
      /* TODO: Notify */
      return;
    }
    var oldStatus = {};
    $.extend(oldStatus, Dogvibes.status);
    $.extend(Dogvibes.status, data.result);
    /* TODO: solve better. Fill in artist info when state is stopped.
     * since this info is not sent from server */
    if(data.result.state == "stopped") {
      data.result.artist = "";
      data.result.album  = "";
      data.result.title  = "";
    }

    /* Walk through interesting status fields and dispatch events if changed */
    if(Dogvibes.status.state != oldStatus.state) {
      $(document).trigger("Status.state");
    }

    if(Dogvibes.status.volume != oldStatus.volume) {
      $(document).trigger("Status.volume");
    }

    if(Dogvibes.status.artist != oldStatus.artist ||
       Dogvibes.status.title  != oldStatus.title  ||
       Dogvibes.status.album  != oldStatus.album  ||
       Dogvibes.status.index  != oldStatus.index) {
      $(document).trigger("Status.songinfo");
    }

    if(Dogvibes.status.elapsedmseconds != oldStatus.elapsedmseconds ||
       Dogvibes.status.duration != oldStatus.duration) {
      $(document).trigger("Status.time");
    }

    if(Dogvibes.status.playlist_id != oldStatus.playlist_id) {
      $(document).trigger("Status.playlist");
    }

    if(Dogvibes.status.playlistversion != oldStatus.playlistversion) {
      $(document).trigger("Status.playlistchange");
    }

    if(Dogvibes.status.elapsedmseconds != oldStatus.elapsedmseconds) {
      $(document).trigger("Status.elapsed");
    }

    /* TODO: add more */
  },
  /****************
   * API functions
   ****************/
  search: function(keyword, Success) {
    var URL = Dogvibes.cmd.search + escape(keyword);
    Dogvibes.server.send(URL, Success);
  },
  getAllPlaylists: function(Success) {
    Dogvibes.server.send(Dogvibes.cmd.playlists, Success);
  },
  getAllTracksInPlaylist:function(id, Success) {
    Dogvibes.server.send(Dogvibes.cmd.playlist + id, Success);
  },
  addToPlaylist: function(id, uri, Success) {
    var URL = Dogvibes.cmd.addtoplaylist + id + "&uri=" + escape(uri);
    Dogvibes.server.send(URL, Success);
  },
  removeFromPlaylist: function(id, pid, Success) {
    var cmd = (id.indexOf(',') == -1) ? Dogvibes.cmd.removeFromPlaylist : Dogvibes.cmd.removeTracksFromPlaylist;
    var URL = cmd + id + "&playlist_id=" + pid;
    Dogvibes.server.send(URL, Success);
  },
  playTrack: function(id, pid, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.playTrack + id + "&playlist_id=" + pid;
    Dogvibes.server.send(URL, Success);
  },
  getAllTracksInQueue: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.playqueue;
    Dogvibes.server.send(URL, Success);
  },
  queue: function(uri, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.queue + escape(uri);
    Dogvibes.server.send(URL, Success);
  },
  queueAlbum: function(uri, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.queueAlbum + escape(uri);
    Dogvibes.server.send(URL, Success);
  },
  addAlbumToPlaylist: function(id, uri, Success) {
    var URL = Dogvibes.cmd.addAlbumToPlaylist + id + "&uri=" + escape(uri);
    Dogvibes.server.send(URL, Success);
  },
  removeTrack: function(id, Success) {
    var cmd = (id.indexOf(',') != -1) ? Dogvibes.cmd.removeTrack : Dogvibes.cmd.removeTracks;
    var URL = Dogvibes.defAmp + cmd + id;
    Dogvibes.server.send(URL, Success);
  },
  play: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.play;
    Dogvibes.server.send(URL, Success);
  },
  queueAndPlay: function(uri, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.queueAndPlay + escape(uri);
    Dogvibes.server.send(URL, Success);
  },
  prev: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.prev;
    Dogvibes.server.send(URL, Success);
  },
  next: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.next;
    Dogvibes.server.send(URL, Success);
  },
  pause: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.pause;
    Dogvibes.server.send(URL, Success);
  },
  createPlaylist: function(name, Success) {
    var URL = Dogvibes.cmd.createPlaylist + name;
    Dogvibes.server.send(URL, Success);
  },
  removePlaylist: function(id, Success) {
    var URL = Dogvibes.cmd.removePlaylist + id;
    Dogvibes.server.send(URL, Success);
  },
  renamePlaylist: function(id, name, Success) {
    var URL = Dogvibes.cmd.renamePlaylist + id + "&name=" + name;
    Dogvibes.server.send(URL, Success);
  },
  setVolume: function(vol, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.setVolume + vol;
    Dogvibes.server.send(URL, Success);
  },
  seek: function(time, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.seek + time;
    Dogvibes.server.send(URL, Success);
  },
  move: function(pid, tid, pos, Success) {
    var URL = Dogvibes.cmd.moveInPlaylist + pid + "&track_id=" + tid + "&position=" + pos;
    Dogvibes.server.send(URL, Success);
  },
  getAlbums: function(query, Success) {
    var URL = Dogvibes.cmd.getAlbums + escape(query);
    Dogvibes.server.send(URL, Success);
  },
  getAlbum: function(uri, Success, Context) {
    var URL = Dogvibes.cmd.getAlbum + escape(uri);
    Dogvibes.server.send(URL, Success, Context);
  },
  getPlayedMilliSecs: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.getPlayedMilliSecs;
    Dogvibes.server.send(URL, Success);
  },
  /* Returns an URL to the album art */
  albumArt: function(artist, album, size) {
    if (artist == '' || album == '') {
      return "";
    }
    return Dogvibes.albumartURL + Dogvibes.cmd.albumArt + escape(album) + "&artist=" + escape(artist) + "&size=" + size;
  },
  vote: function(uri, Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.vote + Dogvibes.dogtag + "&uri=" + escape(uri);
    Dogvibes.server.send(URL, Success);    
  },
  getActivity: function(Success) {
    var URL = Dogvibes.defAmp + Dogvibes.cmd.getActivity;
    Dogvibes.server.send(URL, Success);     
  }
};

window.Dogvibes.defaultStatus = {
  result: {
    artist: "",
    title: "",
    album: "",
    uri: "",
    state: "stopped",
    playlist_id: ""
  },
  error: 0
};
