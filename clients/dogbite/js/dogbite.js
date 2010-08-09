/* Some configuration options */
var Config =  {
  defServer: "http://dogvibes.com",
  defAmp: "/amp/0",
  defAlbumArtURL: "img/dummy.png",
  pollInterval: 1000 /* ms */
};

/* Shortcuts to save some typing */
var d = document;
d.cE  = document.createElement;
d.cT  = document.createTextNode;
d.gID = document.getElementById;

/* UI container objects */
var UI = {
  info: null,
  track: null,
  bottom: null,
  albArt: null,
  playlists: null,
  /* Initialize all objects */
  init: function() {
    UI.info    = d.gID("info");
    UI.track   = d.gID("track");
    UI.bottom  = d.gID("bottom");
    UI.albArt  = d.gID("player");
    UI.playlists = d.gID("home");
    UI.playlist = d.gID("playlist");
    UI.currentlist = d.gID("currentlist");
  },
  /* Misc handy function for creating elements */
  newElement: function (tag, content) {
    var el = d.cE(tag);
    var c;
    if(typeof(content) == "object") {
      c = content;
    }else {
      c = d.cT(content+"");
    }
    el.appendChild(c);
    return el;
  },
  setText: function(obj, text) {
    if(typeof(obj.childNodes[0]) == "undefined") {
      obj.appendChild(d.cT(text));
    }
    else {
      obj.childNodes[0].nodeValue = text+"";
    }
  }
};

/* Create a function for converting msec to time string */
Number.prototype.msec2time = function() {
  var ts = Math.floor(this / 1000);
  if(!ts) { ts=0; }
  if(ts===0) { return "0:00"; }
  var m = Math.round(ts/60 - 0.5);
  var s = Math.round(ts - m*60);
  if (s<10 && s>=0){
    s="0" + s;
  }
  return m + ":" + s;
};

/* The status fields this application is interested in. Also default values */
var defStatus = {
  volume: 0,
  state: "disconnected",
  title: "Not connected",
  artist: "",
  album: "",
  albumArt: "",
  playqueuehash: "",
  playlist_id: false
};

var stopStatus = {
  title: "Nothing to play",
  artist: "",
  album: ""
};

/* Status:
 *
 * Object that fetches server data and dispatches events. This object
 * always contains the latest status data in Status.data */
var Status = {
  timer: null,
  inProgress: false,
  data: { result: defStatus, error: 0 },
  init: function() {
    /* Listen and respond to server connection events */
    $(document).bind("Server.connected", Status.run);
    $(document).bind("Server.error", Status.stop);

    /* Also respond to immediate status request */
    $(document).bind("Status.invalid", Status.get);

    /* Trigger update of info when started */
    $(document).trigger("Status.songinfo");
  },
  run: function() {
    Status.timer = setTimeout(Status.get, Config.pollInterval);
  },
  stop: function() {
    clearTimeout(Status.timer);
    Status.handle({result: defStatus, error: 1});
    Status.data.state = "disconnected";
  },
  get: function() {
    /* Clear any pending request prior to making a new one */
    clearTimeout(Status.timer);
    Server.request(Server.cmd.status, Status.handle);
  },
  handle: function(data) {
    /* Need to save old data before dispatching events */
    var oldStatus = Status.data;
    Status.data = data.result;

    /* TODO: solve better. Fill in artist info when state is stopped.
     * since this info is not sent from server */
    if(data.result.state == "stopped") {
      data.result.artist = stopStatus.artist;
      data.result.album  = stopStatus.album;
      data.result.title  = stopStatus.title;
    }

    /* Reload timer if not disconnected */
    if(data.result.state != "disconnected") {
      Status.timer = setTimeout(Status.get, Config.pollInterval);
    }

    if(data.error !== 0) {
      /* TODO: notify some how */
    }

    /* Walk through interesting status fields and dispatch events if changed*/
    if(Status.data.state != oldStatus.state) {
      $(document).trigger("Status.state");
    }

    if(Status.data.volume != oldStatus.volume) {
      $(document).trigger("Status.volume");
    }

    if(Status.data.artist != oldStatus.artist ||
       Status.data.title  != oldStatus.title  ||
       Status.data.album  != oldStatus.album  ||
       Status.data.albumArt != oldStatus.albumArt) {
      $(document).trigger("Status.songinfo");
    }

    if(Status.data.elapsedmseconds != oldStatus.elapsedmseconds ||
       Status.data.duration != oldStatus.duration) {
      $(document).trigger("Status.time");
    }

    if(Status.data.playlist_id != oldStatus.playlist_id ||
       Status.data.playqueuehash != oldStatus.playqueuehash) {
      $(document).trigger("Status.playlist");
    }
  }
};

/* Server:
 *
 * Object that manages server connection. */
var Server = {
  url: null, /* TODO: load from cookie */
  cmd: {
    status: Config.defAmp + "/getStatus",
    prev:   Config.defAmp + "/previousTrack",
    play:   Config.defAmp + "/play",
    playTrack: Config.defAmp + "/playTrack?nbr=",
    pause:  Config.defAmp + "/pause",
    next:   Config.defAmp + "/nextTrack",
    seek:   Config.defAmp + "/seek?mseconds=",
    volume: Config.defAmp + "/setVolume?level=",
    albumArt: "/dogvibes/getAlbumArt?size=320&artist=",
    playlists: "/dogvibes/getAllPlaylists",
    playlist: "/dogvibes/getAllTracksInPlaylist?playlist_id=",
    playqueue: Config.defAmp + "/getAllTracksInQueue"
  },
  init: function() {
    var temp;
    /* Default state */
    $(document).trigger("Server.error");

    /* Do we have a server? Otherwise ask user to enter URL */
    if((temp = getCookie("dogvibes.server")) != ""){
        Config.defServer = temp;
    }
    if(!Server.url) {
      Server.url = prompt("Enter Dogvibes server URL:", Config.defServer);
    }
    /* Try to connect */
    Server.request(Server.cmd.status, Server.connected);
  },
  request: function(Command, Success, Error) {
    /* Setup default callbacks */
    if(typeof(Success) == "undefined") {
      Success = Status.get;
    }
    if(typeof(Error) == "undefined") {
      Error = Server.error;
    }
    $.jsonp({
      url: Server.url + Command,
      error: Error,
      success: Success,
      callbackParameter: "callback"
    });
  },
  connected: function(json) {
    /* Let people know that we have working connection */
    $(document).trigger("Server.connected");
    /* Save server in cookie for next time */
    setCookie("dogvibes.server", Server.url, 365);
    /* FIXME: not nice. Trigger an info update since we've got the
       latest status at this point */
    Status.handle(json);

  },
  error: function(data, text) {
    $(document).trigger("Server.error");
    /* */
    alert("Ooops! No server!");
  }
};

/* SongInfo:
 *
 * Handles artist/trackname updates (upper bar) in the UI etc. */

var SongInfo = {
  ui: Array(),
  init: function() {
    /* Create UI objects that this module controls */
    SongInfo.ui.time = d.cE('ul');
    var ul = d.cE('ul');

    /* Back button */
    SongInfo.ui.back = d.cE('a');
    SongInfo.ui.back.className = 'music_button left';
    //SongInfo.ui.back.onclick = function() { alert('Sorry, not yet!'); };
    SongInfo.ui.back.href = "#home";

    SongInfo.ui.list = d.cE('a');
    SongInfo.ui.list.className = 'list_button right';
    //SongInfo.ui.back.onclick = function() { alert('Sorry, not yet!'); };
    SongInfo.ui.list.href = "#currentlist";


    /* Track data */
    SongInfo.ui.artist = d.cE('li');
    ul.appendChild(SongInfo.ui.artist);

    SongInfo.ui.title = d.cE('li');
    SongInfo.ui.title.className = "highlight";
    ul.appendChild(SongInfo.ui.title);

    SongInfo.ui.album = d.cE('li');
    ul.appendChild(SongInfo.ui.album);

    /* Append to top menu */
    UI.info.appendChild(SongInfo.ui.back);
    UI.info.appendChild(ul);
    UI.info.appendChild(SongInfo.ui.list);

    /* Time and slider */
    SongInfo.ui.elapsed = d.cE('li');
    SongInfo.ui.elapsed.className = "time";
    SongInfo.ui.time.appendChild(SongInfo.ui.elapsed);

    SongInfo.ui.slider = d.cE('li');
    SongInfo.ui.slider.className = "slider";
    SongInfo.ui.time.appendChild(SongInfo.ui.slider);

    SongInfo.ui.total = d.cE('li');
    SongInfo.ui.total.className = "time";
    SongInfo.ui.time.appendChild(SongInfo.ui.total);

    /* Append to 'trackNo and time' info */
    UI.track.appendChild(SongInfo.ui.time);

    /* Setup event listeners */
    $(document).bind("Server.error", SongInfo.hide);
    //$(document).bind("Server.connected", SongInfo.show);
    $(document).bind("Status.songinfo", SongInfo.set);
    $(document).bind("Status.time", SongInfo.time);
  },
  set: function() {
    /* Update UI labels with lastest song info  */
    UI.setText(SongInfo.ui.artist, Status.data.artist);
    UI.setText(SongInfo.ui.album, Status.data.album);
    UI.setText(SongInfo.ui.title, Status.data.title);
    /* Update album art */
    var imgUrl = (Server.url == null ||
                  Status.data.album == '' ||
                  typeof(Status.data.album) == "undefined")
                 ?
                 Config.defAlbumArtURL
                 :
                 Server.url + Server.cmd.albumArt + escape(Status.data.artist) + "&album=" + escape(Status.data.album);
    $(UI.albArt).css('background-image', 'url(' + (imgUrl) + ')');
  },
  time: function() {
    /* TODO: implement slider */
    var elapsed, duration;
    /* We don't have time information when state is stopped */
    if(Status.data.state == "stopped" ||
       Status.data.state == "disconnected") {
      elapsed = "";
      duration = "";
    }
    else {
      elapsed  = Status.data.elapsedmseconds.msec2time();
      duration = (Status.data.duration).msec2time();
    }

    UI.setText(SongInfo.ui.elapsed, elapsed);
    UI.setText(SongInfo.ui.total, duration);

  },
  show: function() {
    $(UI.track).show();
    UI.albArt.className = "";
  },
  hide: function() {
    $(UI.track).hide();
    UI.albArt.className = "none";
  }
};

/* PlayControl:
 *
 * Handles playback and volume
 */
var PlayControl = {
  ui: Array(),
  init: function() {
    /* Create UI objects that this module controls */
    var li;
    PlayControl.ui.volume = d.cE('div');
    PlayControl.ui.volume.id = "volume";

    PlayControl.ui.ctrl = d.cE('ul');
    PlayControl.ui.ctrl.id = "playback";

    PlayControl.ui.prev = d.cE('span');
    PlayControl.ui.prev.className = "prev";
    li = UI.newElement('li', PlayControl.ui.prev);
    PlayControl.ui.ctrl.appendChild(li);

    PlayControl.ui.play = d.cE('span');
    PlayControl.ui.play.className = "play";
    li = UI.newElement('li', PlayControl.ui.play);
    PlayControl.ui.ctrl.appendChild(li);

    PlayControl.ui.next = d.cE('span');
    PlayControl.ui.next.className = "next";
    li = UI.newElement('li', PlayControl.ui.next);
    PlayControl.ui.ctrl.appendChild(li);

    UI.bottom.appendChild(PlayControl.ui.ctrl);
    UI.bottom.appendChild(PlayControl.ui.volume);

    /* Setup events */
    $(document).bind("Status.volume", PlayControl.volume);
    $(document).bind("Status.state", PlayControl.state);
    $(document).bind("Server.connected", PlayControl.show);
    $(document).bind("Server.error", PlayControl.hide);
  },
  volume: function() {
    /* TODO: Implement slider */
    UI.setText(PlayControl.ui.volume, "Volume: " + Math.round(Status.data.volume*100),0);
  },
  /* Update to the correct state */
  state: function() {
    if(Status.data.state == "playing") {
      $(PlayControl.ui.ctrl).addClass('playing');
    }
    else {
      $(PlayControl.ui.ctrl).removeClass('playing');
    }

    /* Hide time info when stopped */
    if(Status.data.state == "stopped" |
       Status.data.state == "disconnected") {
      SongInfo.hide();
    }
    else {
      SongInfo.show();
    }
  },
  show: function() {
    $(PlayControl.ui.ctrl).removeClass("disabled");
    /* Make controlls clickable */
    $(PlayControl.ui.prev).click(function() { Server.request(Server.cmd.prev); return false; });
    $(PlayControl.ui.play).click(function() {
      Server.request(
        Status.data.state == "playing" ?
        Server.cmd.pause :
        Server.cmd.play
      );
      return false;
    });
     $(PlayControl.ui.next).click(function() { Server.request(Server.cmd.next); return false; });

  },
  hide: function() {
    $(PlayControl.ui.ctrl).addClass("disabled");
    /* Make controls unclickable */
    $(PlayControl.ui.prev).unbind();
    $(PlayControl.ui.play).unbind();
    $(PlayControl.ui.next).unbind();
  }
};

/* Playlists */

var Playlists  = {
  activeList: "",
  nbrOfSongs: 0,
  init: function() {
    $(document).bind("Server.connected", Playlists.fetch);
    $(document).bind("Status.playlist", Playlists.getListContent);
  },
  fetch: function() {
    Server.request(Server.cmd.playlists, Playlists.update);
  },
  update: function(json) {
    var lists = json.result;
    var li, a;
    $(UI.playlists).empty();
    /* Add playqeueu item */

    a = UI.newElement('a', 'Playqueue');
    a.href = "#playlist";
    a._pid = "-1";
    a._name = "Playqueue";
    a.onclick = Playlists.getListContent;
    li = UI.newElement('li', a);
    UI.playlists.appendChild(li);

    for(var i in lists) {
      a  = UI.newElement('a', lists[i].name);
      a.href = "#playlist";
      a._pid = lists[i].id;
      a._name = lists[i].name;
      a.onclick = Playlists.getListContent;

      li = UI.newElement('li', a);
      UI.playlists.appendChild(li);
    }
  },
  getListContent: function() {
    /* Clear list */
    $(UI.playlist).empty();
    var pid;
    /* Only update from event if active list is updated */
    if(typeof(this._pid) == "undefined") {
      if(Status.data.playlist_id === Playlists.activeList) {
        pid = Playlists.activeList;
      }
      else {
        return;
      }
    }
    else {
      pid = this._pid;
    }
    /* Get items, TODO: load indicator */
    var cmd = pid == -1 ?
      Server.cmd.playqueue
      :
      Server.cmd.playlist + pid;
    UI.playlist.title = this._name;
    /* Set currently viewed playlist */
    Playlists.activeList = pid;
    Server.request(cmd, Playlists.setListContent);
  },
  setListContent: function(json) {
    var items = json.result;
    var a, li, cnt = 0;

    for(var i in items) {
      a  = UI.newElement('a', items[i].title);
      a.href = "#player";
      a._id = items[i].id;
      a.onclick = Playlists.playItem;
      li = UI.newElement('li', a);
      if(a._id == Status.data.index &&
         Playlists.activeList == Status.data.playlist_id) {
        li.setAttribute('selected','true');
      }
      UI.playlist.appendChild(li);
    }
    Playlists.nbrOfSongs = cnt;
  },
  playItem: function() {
    var item = this._id;
    Server.request(Server.cmd.playTrack + item + "&playlist_id=" + Playlists.activeList);
  }
};

var CurrentList = {
  nbrOfItems: 0,
  ui: Array(),
  init: function() {
    CurrentList.ui.trackNo = d.cE('strong');
    UI.track.appendChild(CurrentList.ui.trackNo);

    $(document).bind("Status.playlist", CurrentList.fetch);
    $(document).bind("Status.songinfo", CurrentList.set);    
  },
  fetch: function() {
    var pid = Status.data.playlist_id;
    if(!pid) { return; }
    var cmd = pid == "-1" ?
      Server.cmd.playqueue
      :
      Server.cmd.playlist + pid;
    Server.request(cmd, CurrentList.update);
  },
  update: function(json) {
    var items = json.result;
    var li, a, cnt = 0;
    CurrentList.nbrOfItems = items.length;
    $(UI.currentlist).empty();    
    for(var i in items) {
      a  = UI.newElement('a', items[i].title);
      a.href = "#player";
      a._id = cnt++;
      a.onclick = CurrentList.playItem;
      li = UI.newElement('li', a);
      li.id = "CurrentList-item-" + a._id;
      UI.currentlist.appendChild(li);
    }
    CurrentList.set();    
  },
  playItem: function() {
    var item = this._id;
    Server.request(Server.cmd.playTrack + item + "&playlist_id=" + Status.data.playlist_id);
  },
  set: function() {
    $("li", UI.currentlist).removeClass('toggle');
    UI.setText(CurrentList.ui.trackNo, (Status.data.index + 1) + " of " + CurrentList.nbrOfItems);
    $("#CurrentList-item-"+Status.data.index).addClass('toggle');
  }
};

/* Let's begin when document is ready */
window.onload = function() {
  /* UI needs to be initialized first! */
  UI.init();
  CurrentList.init();
  SongInfo.init();
  PlayControl.init();
  Status.init();
  Playlists.init();
  /* Finally start server connection */
  Server.init();

  /* Hide iPhone status bar */
  window.scrollTo(0, 1);
};
