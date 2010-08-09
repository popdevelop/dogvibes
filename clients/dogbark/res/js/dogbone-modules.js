/*
 * Modules for handling playlists, searches, etc...
 */

var Config = {
  defaultUser: "sswc",
  defaultServer: "dogvib.es",
  defaultProtocol: ["http", "http"], //Order to try protocols
  maxActivity: 10
};

// XXX: Get rid of this in the future
var ResultTable = function(config) {
  var self = this;
  /* Default configuration */
  this.options = {
    name: "Table",
    idTag: "id",
    highlightClass: "playing",
    selectable: true,
    click: function(e) {
      $(document).dblclick();
      var tbl = $(this).data('self');
      tbl.selectMulti = e.shiftKey ? true : false;
      var nbr = $(this).data('nbr');
      tbl.selectItem(nbr);
    },
    dblclick: $.noop,
    callbacks: {
      album: function(element) {
        var a = $('<a/>').attr('href', '#album/' + element.data.album_uri);
        element.contents().wrap(a);
      },      
      artist: function(element) {
        var a = $('<a/>').attr('href', '#artist/' + element.text());
        element.contents().wrap(a);
      }    
    }
  };
  
  /* Set user configuration */
  $.extend(true, this.options, config);
  
  this.ui = {
    content: "#" + self.options.name + "-content",
    items  : "#" + self.options.name + "-items"
  };  
  
  /* Some properties */
  this.items = [];
  this.data  = {};
  this.selectedItem = false;
  this.selectedItems = [];
  this.fields = [];
  this.selectMulti = false;
  this.id2index = {};
  
  /* Configure table fields by looking for table headers if not provided
   * in options */
  if(typeof(this.options.fields) == "undefined") {
    $(".template", self.ui.content).children().each(function(i, el) {
      if("id" in el) {
        var field = el.id.removePrefix(self.options.name + "-");
        if(field !== false) {
          self.fields.push(field);
        }
      }
    });
  } else {
    this.fields = this.options.fields;
  }
  
  if(!self.options.selectable) {
    self.options.click = $.noop;
  }
  
  /***** Methods *****/
  this.display = function() {
    var self = this;
    /* Reset */
    self.selectedItems = [];
    $(self.ui.items).empty();
    self.id2index = [];
        
    /* Fill with new items */
    $(self.items).each(function(i, el) {
      var tr = $("<tr></tr>");
      var id = self.options.idTag in el ? el[self.options.idTag] : i;
      /* Store some data */
      tr.data('id', id);
      tr.data('nbr', i);
      tr.data('self', self);
      tr.attr('id', self.options.name+"-item-nbr-"+i);
      /* always add uri */
      if("uri" in el) { tr.data('uri', el.uri); }
      $(self.fields).each(function(j, field) {
        var content = $("<td></td>");
        if(field in el) {
          var value = el[field];
          /* FIXME: assumption: Convert to time string if value is numeric */
          if(typeof(value) == "number") {
            value = value.msec2time();
            content.addClass("time");
          }
          content.append(value);
        }
        if(field in self.options.callbacks) {
          content.id = id;
          content.nbr = i;
          content.tbl = self;
          content.data = el;
          self.options.callbacks[field](content);
        }        
        tr.append(content);
      });
      tr.click(self.options.click);
      tr.dblclick(self.options.dblclick);
      $(self.ui.items).append(tr);
      /* Save rows internally and build map over id --> index */
      self.data[i] = tr;
      self.id2index[id] = i;
    });
    
    $("tr:visible",this.ui.items).filter(":odd").addClass("odd");
        
    /* Update tablesorter */
    $(self.ui.content).trigger("update");
  };
  
  this.empty = function() {
    $(this.ui.items).empty();
  };
  
  this.selectItem = function(index) {
    var self = this;
    index = parseInt(index, 10);
    if(!self.selectMulti) {
      self.deselectAll();
    }
    if(index > self.items.length) { return; }
    if(self.selectMulti===false || self.selectedItem===false) {
      self.selectedItem = index;
    }

    /* Create the selection range */
    var min = self.selectedItem < index ? self.selectedItem : index;
    var max = self.selectedItem < index ? index : self.selectedItem;
    self.selectedItems = [];
    for(var i = min; i <= max; i++) {
      self.selectedItems.push(i);
      self.data[i].addClass("selected");
    }
  };
  this.deselectAll = function() {
    this.selectedItem = false;
    this.selectedItems = [];
    $("tr", this.ui.items).removeClass("selected");
  };
  this.clearHighlight = function(cls) {
    cls = typeof(cls) == "undefined" ? this.options.highlightClass : cls;
    $("tr", this.ui.items).removeClass(cls);  
  };
  this.highlightItem = function(index, cls) {
    if(typeof(cls) == "undefined") { cls = this.options.highlightClass; }
    /* Try index first */
    if(index in this.data) {
      this.data[index].addClass(cls);
      return;
    }
    /* Next try id */
    if(index in this.id2index) {
      var idx = this.id2index[index];
      this.data[idx].addClass(cls);
      return;
    }
  };
};


/**************************
 * Prototype extensions
 **************************/

/* remove a prefix from a string */
String.prototype.removePrefix = function(prefix) {
  if(this.indexOf(prefix) === 0) {
    return this.substr(prefix.length);
  }
  return false;
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

/* Create a string with relative time (eg. '15 minutes ago' etc) */
Number.prototype.relativeTime = function() {
  var now = new Date().getTime();
  now /= 1000; //msec --> sec
  var names = ['seconds', 'minutes', 'hours'];
  var diff = Math.floor(now - this);
  if(diff < 10) {
    return "just now";
  }
  for(var i = 0; i < 3; i++) {
    if(diff < 60) {
      return diff + " " + names[i] + " ago";
    } 
    diff = Math.floor(diff / 60);
  }
  return "long time ago";
};

/**************************
 * Modules 
 **************************/

var Playqueue = {
  ui: {
    page: '#',
    info: '#Playqueue-info',
    tracklist: '#tracks'
  },
  items: { error: 0 },
  init: function() {
    $(Playqueue.ui.info).text('Play queue not available when offline').hide();

    $(document).bind("Status.playlistchange", function() { Playqueue.fetch(); });    
    $(document).bind("Server.connected", function() {
      $(Playqueue.ui.info).hide();
      Playqueue.fetch();      
    });
    $(document).bind("Server.error", function() {
      $(Playqueue.ui.tracklist).empty();
      $(Playqueue.ui.info).show();     
    });
    $(document).bind("User.info", function(){
      Playqueue.set();
    }); 
    $(document).bind("Status.state", function(){
      Playqueue.set();
    });     
  },  
  fetch: function() {
    if(Dogvibes.server.connected) { 
      Dogvibes.getAllTracksInQueue("Playqueue.draw");
    }
  },
  // Render list items
  draw: function(json) { 
    if(json.error !== 0) {
      return;
    }
    $(Playqueue.ui.tracklist).empty();
    var num = 0;
    var item;
    Playqueue.items = json;
    $(json.result).each(function(i, el) {
      var active = i === 0 ? true : false; //XXX: improve!
      num++;
      item = Playqueue._newItem(el, active);
      $(Playqueue.ui.tracklist).append(item);
    });
    if(num === 0) {
      item = $("<li></li>").attr("class", "noTracks").text("No tracks to be played. Please add.");
      $(Playqueue.ui.tracklist).append(item);
    }
    item.addClass("last");
    Playqueue.setState();
  },
  // Update play state etc.
  set: function() {
    Playqueue.draw(Playqueue.items);
  },
  setState: function(){
    if(Dogvibes.status.state == 'playing'){
      $('#playIndicator').addClass('playing');
    }
    else {
      $('#playIndicator').removeClass('playing');      
    }  
  },
  // Generate a list item
  _newItem: function(json, active) {
    //XXX: Piggy style
    var cls = "";
    var artSize = 48;
    
    if(active) { 
      cls = "first playing"; 
      artSize = 150;
    }
    var item = $("<li></li>").attr("class", "gradient " + cls);
    $("<img>")
      .attr("src", Dogvibes.albumArt(json.artist, json.album, artSize))
      .click(function() { 
        window.location.hash = "#album/" + json.album_uri; 
      })      
      .appendTo(item);
    
    if(active) {
      $("<h3></h3>").text("now playing").appendTo(item);
      $("<em></em>").text(json.title).appendTo(item);
      $("<span></span>")
        .click(function() { 
          window.location.hash = "#artist/" + json.artist; 
        })
        .text(json.artist).appendTo(item);
      $("<span></span>").attr("class", "album")
        .text(json.album)
        .click(function() { 
          window.location.hash = "#album/" + json.album_uri; 
        })        
        .appendTo(item);
      $("<div></div>")
        .attr("id", "playIndicator")
        .appendTo(item);
    }
    else {
      var text = $("<div></div>").addClass("trackText").appendTo(item);
      $("<span></span>").text(json.title).appendTo(text);
      $("<span></span>").text(" by ").addClass("weak").appendTo(text);
      $("<span></span>").text(json.artist).appendTo(text);
      item.append(voteButton(json));
    }
    
    // Votes
    var votes = json.voters.length > 4 ? 4 : json.voters.length;
    var sum = votes === 0 ? "No" : votes;
    if(json.voters.length > votes) { sum = sum + "+"; }    
    sum = sum + " vote" + (votes == 1 ? "" : "s");
    var voteList = $("<ul></ul>").attr("class", "votes").appendTo(item);
    for(var i = 0; i < votes; i++) {
      var li = $("<li></li>").appendTo(voteList);
      $("<img>")
        .attr("src", json.voters[i].avatar_url)
        .attr("title", json.voters[i].username)
        .appendTo(li);
    }
    $("<li></li>").attr("class", "sum").text(sum).appendTo(voteList);
    
    return item;
  }
};

//XXX: move somewhere
function voteButton(json) {
  //Check if user has voten on this track
  
  //XXX: Check against currently playing track.
  //     Should not display button at all if same
  
  var voted = User.votes[json.uri] === true;
  var item;
  item = $("<input>")
    .attr("type", "submit")
    .attr("value", "vote")
    .addClass('voteButton');
  
  // Generate correct button
  if(voted) {
    item.click(function() {
      Dogvibes.unVote(json.uri);
      $(this).unbind("click").addClass("voting");
      return false;
    }).addClass("undo");  
  } else {
    item.click(function() {
      if(User.info.votes > 0) {
        Dogvibes.vote(json.uri);
        $(this).unbind("click").addClass("voting");        
      }
      return false;
    }); 
  }
  return item;
}

var User =  {
  info: {},
  votes: {}, //uri hashlist for quick compare
  init: function() {
    $(document).bind("Status.activity", function() {
      User.update();
    });
  },
  update: function() {
    // Request user info
    Dogvibes.getUserInfo("User.set");
  },
  set: function(json) { 
    if(json.error !== 0) {
      $("#User-votes").text("Failed to get user info :(");
      return false;
    }
    // Create the hash list
    User.votes = {};
    $(json.result.voted_tracks).each(function(i, el) {
      User.votes[el.uri] = true;
    });
    // Set info and dispatch event
    User.info = json.result;
    $(document).trigger("User.info");
    
    // Update UI objects
    var vts = User.info.votes == 1 ? " vote" : " votes";
    var info = $("<span></span>").addClass("user").text(User.info.username);
    $("#User-votes").text(User.info.votes + vts + " left for ").append(info);
  }
};

var Activity = {
  ui: {
    list: "#Activity-list"
  },
  items: {error: 0},
  init: function() {
    $(document).bind("Server.connected", function() {
      Activity.fetch();      
    });
    $(document).bind("Status.activity", function() {
      Activity.fetch();      
    });
    //Re-draw list on vote change
    $(document).bind("User.info", function() {
      Activity.set();      
    });
  },
  fetch: function() {
    if(Dogvibes.server.connected) {
      Dogvibes.getActivity(Config.maxActivity, "Activity.draw");
    }
  },
  draw: function(json) {
    $(Activity.ui.list).empty();
    if(json.error !== 0) {
      $("<li></li>").addClass("first last").text("Oops, something went wrong").appendTo($(Activity.ui.list));
      return;
    }
    Activity.items = json;
    var num = 0;
    var item;
    $(json.result).each(function(i, el) {
      num++;
      item = Activity._newItem(el);
      if(i === 0) { item.attr("class", "first"); }
      $(Activity.ui.list).append(item);
    });
    
    if(num === 0) {
      item = $("<li></li>").addClass("first").text("No updates");
      $(Activity.ui.list).append(item);
    }
    item.addClass("last");
      
  },
  set: function() {
    Activity.draw(Activity.items);
  },
  _newItem: function(json) {
    var item = $("<li></li>").addClass("gradient");
    $("<img></img>").attr("src", json.avatar_url).appendTo(item);
    item.append(voteButton(json));
    $("<span></span>").addClass("user").text(json.user).appendTo(item);
    $("<span></span>").addClass("weak").text(" voted for ").appendTo(item);
    $("<span></span>").text(json.title).appendTo(item);
    $("<span></span>").addClass("weak").text(" by ").appendTo(item);
    $("<span></span>").text(json.artist).appendTo(item);        
    $("<span></span>").addClass("time").text(json.time.relativeTime()).appendTo(item);
    return item;
  }
};

// Display appropriate popup depending on server state
var ConnectionIndicator = {
  message: false,
  init: function() {
    $(document).bind("Server.connecting", function() {
      Popup.message("Trying to connect you...", true);
    });
    $(document).bind("Server.error", function() {
    Popup.message("Sorry, there seems to be a problem with the connection to dogvibes. Please check your dog or reload the page", false);
    });
    $(document).bind("Server.connected", function() {
      Popup.hide();
    });
  }
};

// XXX: Use this for playing track instead of Playqueue or remove
var TrackInfo = {
  ui: {
    artist  : "#TrackInfo-artist",
    title   : "#TrackInfo-title",
    albumArt: "#TrackInfo-albumArt"
  },
  init: function() {
    if($(TrackInfo.ui.artist) && $(TrackInfo.ui.title)) {
      $(document).bind("Status.songinfo", TrackInfo.set);
    }
  },
  set: function() {
    $(TrackInfo.ui.artist).text(Dogvibes.status.artist);
    $(TrackInfo.ui.title).text(Dogvibes.status.title);
    var img = Dogvibes.albumArt(Dogvibes.status.artist, Dogvibes.status.album, 180);
    /* Create a new image and crossfade over */
    var newImg = new Image();
    newImg.src = img;
    newImg.id  = 'TrackInfo-newAlbumArt';
    /* Don't show image until fully loaded */
    $(newImg).load(function() {
      $(newImg)
        .appendTo('#currentsong')
        .fadeIn(500, function() {
          $(TrackInfo.ui.albumArt).remove();
          $(newImg).attr("id", "TrackInfo-albumArt");
        });
    });
  }
};


var Search = {
  ui: {
    form:    "#Search-form",
    input:   "#Search-input",
    page   : "#search",
    info   : "#Search-info",
    result : "#Search-content"
  },
  searches: [],
  param: "",
  items: {error: 0}, // Save search results
  init: function() {
    /* Init search navigation section */
    $(document).bind("Page.search", Search.setPage);
    
    $(document).bind("Status.songinfo", Search.set);
    $(document).bind("User.info", function() { Search.set(); });
    
    /* Handle offline/online */
    $(document).bind("Server.error", function() {
      $(Search.ui.page).removeClass();
      $(Search.ui.info).text('Search not available when offline').show();
    });
    $(document).bind("Server.connected", function() {
      $(Search.ui.info).hide(); 
      Search.setPage();
    });

    $(Search.ui.form).submit(function(e) {
      var val = $("#Search-input").val();
      if(val != "") {
        Search.doSearch($("#Search-input").val());
      }
      e.preventDefault();
      return false;
    });
  },
  setPage: function() {
    /* See if search parameter has changed. If so, reload */
    if(Dogvibes.server.connected &&
       Dogbone.page.param != Search.param) {
      Search.param = Dogbone.page.param;
      $(Search.ui.page).addClass("loading");
      $(Search.ui.result).empty();
      $(Search.ui.info).hide();
      if(Search.param != "") {
        Dogvibes.search(Search.param, "Search.handleResponse");
      }
    }
  },
  doSearch: function(keyword) {
    window.location.hash = "#search/"+keyword;
  },
 
  handleResponse: function(json) {
    $(Search.ui.page).removeClass("loading");  
    if(json.error !== 0) {
      $("<li></li>")
        .text("Oops! something went wrong")
        .addClass("first last")
        .appendTo($(Search.ui.result));
      return false;
    }
    Search.items = json; // Save for later
    /* Any results? */
    if(json.result.length === 0) {
      $(Search.ui.info)
        .text('Sorry, no matches for "'+Dogbone.page.param+'"')
        .show();
    }
    // Build list
    var num = 0;
    var item;
    $(json.result).each(function(i, el){
      item = Search._newItem(el);
      if(i === 0) { item.addClass("first"); }
      $(Search.ui.result).append(item);
      num++;
    });
    
    if(num === 0) {
      item = $("<li></li>")
        .text("Sorry, could not find anything")
        .addClass("first");
    }
    item.addClass("last");
  },
  set: function() {
    // Re-draw list (uggly/easy way...)
    if(Dogbone.page.id == 'search') {
      $(Search.ui.result).empty();
      Search.handleResponse(Search.items);
    }
  },
  _newItem: function(json) {
    var item = $("<li></li>");
    $("<span></span>").addClass("title").text(json.title).appendTo(item);
    $("<span></span>").text(" by ").appendTo(item);
    $("<a></a>")
      .attr("href", "#artist/"+json.artist)
      .text(json.artist)
      .appendTo(item);
    item.append(voteButton(json));

    return item;
  }
};


/* Combined handler for Artist/album view. TODO: Maybe split up */
var Artist = {
  ui:  {
    artistInfo: "#Artist-info",
    albumInfo: "#Album-info"   
  },
  albums: {
    data: {},
    items: [],
    chunkSize: 10, //Number of albums to load at a time
    leftToDisplay: 0 //Number of albums left to display
  },
  album: false,
  currentArtist: "",
  init: function() {
    $(document).bind("Page.artist", Artist.setPage);
    $(document).bind("Page.album", function() { Artist.setPage(); });
    
    $(document).bind("Status.songinfo", Artist.set);
    $(document).bind("Status.state", function() { Artist.set(); });
    
    /* Offline info */
    $(document).bind("Server.connected", function() { 
      $(Artist.ui.artistInfo).hide();
      $(Artist.ui.albumInfo).hide();      
      Artist.setPage(); 
    });
    $(document).bind("Server.error", function() { 
      Artist.currentArtist = "";
      $("#artist").empty();
      $("#album").empty();      
      $('<div></div>')
        .text('View not available when offline')
        .attr('id', 'Artist-info')
        .appendTo("#artist");
      $('<h3></h3>')
        .text('View not available when offline')
        .attr('id', 'Album-info')
        .appendTo("#album");        
    });
  },
  setPage: function() {
    if(!Dogvibes.server.connected) { return; }
    /* FIXME: clean up this mess */
    if(Dogbone.page.id == "album") {   
      var album = Dogbone.page.param;
      $("#album").empty();
      Dogvibes.getAlbum(album, "Artist.setAlbum");
    }
    else if(Dogbone.page.id == "artist" && Artist.currentArtist != Dogbone.page.param){
      Artist.currentArtist = Dogbone.page.param;
      /* Reset and fetch new data */
      Artist.albums.items = [];
      Artist.albums.data = {};
      $('#artist')
        .empty()
        .append('<h2>'+unescape(Dogbone.page.param)+'</h2>');
      Dogvibes.getAlbums(Dogbone.page.param, "Artist.display");
    }
  },
  setAlbum: function(data) {  
    Artist.album = new AlbumEntry(data.result, { albumLink: false });
    $("#album").append(Artist.album.ui);  
    Artist.album.set(data);
    Artist.set(); 
  },
  display: function(data) {
    if(data.error > 0) { return false; }
    
    /* Fill in data */
    Artist.albums.other = false;
    Artist.albums.data = data.result;
    Artist.albums.leftToDisplay = data.result.length;
    
    /* Any results? */
    if(data.result.length === 0) {
      $('<p></p>').text('No albums for artist').appendTo('#artist');
      return;
    }

    /* FIXME: will this always work? */
    if(Dogbone.page.param == data.result[0].artist) {
      $('<h3></h3>').text("Albums").appendTo('#artist');
    }
    /* Display first chunk of albums */
    Artist.displayMore();
  },
  displayMore: function() {
    /* Display another chunk of albums */
    var offset = Artist.albums.data.length - Artist.albums.leftToDisplay;
    var maxIdx = Math.min(Artist.albums.leftToDisplay, Artist.albums.chunkSize) + offset;
    Artist.albums.leftToDisplay -= Artist.albums.chunkSize;
    var element = false;
    for(var i = offset; i < maxIdx; i++) {
      element = Artist.albums.data[i];
      if(!Artist.albums.other && element.artist != Dogbone.page.param) {
        Artist.albums.other = true;
        $('<h3></h3>')
          .text("Appears on")
          .appendTo('#artist');
      }
      var idx = Artist.albums.items.length;
      Artist.albums.items[idx] = new AlbumEntry(element, { onLoaded: Artist.albumCallback });
      $('#artist').append(Artist.albums.items[idx].ui);
      
      /* Get tracks for album, since we don't get them directly */
      /* FIXME: solve context problem nicer */
      Dogvibes.getAlbum(element.uri, "Artist.albums.items["+idx+"].set", Artist.albums.items[idx]);      
    }
  },
  set: function() {
    return;    
  },
  /* Things to do when an album has loaded */
  albumCallback: function() {
    return;
  }
};

// Monitor scroll position. Invoke handler if at bottom
var ScrollHandler = {
  /* Different handlers for pages */
  handlers: {
    artist: Artist.displayMore
  },
  container: false,
  init: function() {
    /* Invoke action on scroll bottom */
    $("#viewport").scroll(function() { ScrollHandler.checkScroll(); });  
    ScrollHandler.container = $("#viewport");
  },
  checkScroll: function() {
    if(Dogbone.page.id in ScrollHandler.handlers) {
      if(ScrollHandler.container[0].scrollHeight - ScrollHandler.container.height() - ScrollHandler.container.scrollTop() <= 0) {
        ScrollHandler.handlers[Dogbone.page.id]();
      }
    }  
  }
};

/*
 * Class for displaying/fetching an album from uri
 */
var AlbumEntry = function(entry, options) {
  var self = this;
  this.options = {
    albumLink: true,
    onLoaded: $.noop
  };
  $.extend(this.options, options);
  this.tableName = entry.uri.replace(/:/g, '_');
  this.tableName = this.tableName.replace(/\//g, '');
  this.ui = 
    $('<div></div>')
    .addClass('loading')
    .addClass('AlbumEntry');
  var title = 
    $('<h4></h4>')
    .appendTo(this.ui);
  var art = 
    $('<div></div>')
    .addClass('AlbumArt')
    .appendTo(this.ui);
  var artimg = 
    $('<img></img>')
    .attr('src', Dogvibes.albumArt(entry.artist, entry.name, 130))
    .data('album_uri', entry.uri)
    /* Fade in when loaded */   
    .hide()
    .load(function() {
      $(this).fadeIn(500);
    })
    .dblclick(function() {
      var uri = $(this).data("album_uri");
      if(uri) {
        Dogvibes.queueAlbum(uri);
      } 
    })
    .appendTo(art);
    
  /* Clickable album? */
  if(this.options.albumLink) {
      $('<a />')
      .attr('href', "#album/" + entry.uri)
      .text(entry.name + ' ('+entry.released+')')
      .appendTo(title);
    artimg.wrap(
      $('<a></a>')
      .attr('href', "#album/" + entry.uri)
    );
  } else {
    title.text(entry.name + ' ('+entry.released+')');
  }
  
  /* Create the first table */
  this.resTbl = [];

  /****** Some functions ******/
  this.createTable = function(id) {
    /* Create table */
    var name = this.tableName + "_" + id;
    var table =  
      $('<table></table>')
      .attr('id', name +"-content")
      .data('self', this)
      .addClass('theme-tracktable')
      .appendTo(this.ui);
    var items = $('<tbody></tbody>').attr('id', name+'-items').appendTo(table);  
    return new ResultTable({ 
      name: name,
      idTag: 'uri',
      fields: [ 'track_number', 'title', 'duration' ],
      dblclick: function() {
        var uri = $(this).data('uri');
        Dogvibes.vote(uri);    
      },
      callbacks: {
        track_number: function(element) {
          element.addClass('trackNo');
        }
      }
    });    
  };
  this.set = function(data) {
    if(data.error > 0) { return; }
    /* XXX: compensate for different behaviours in AJAX/WS */
    var self = typeof(this.context) == "undefined" ? this : this.context;
    var discs = [];
    /* Split album into several discs, if any */
    var prev_disc = 0;
    var curr_disc = 0;
    for(var i in data.result.tracks) {
      curr_disc = data.result.tracks[i].disc_number;
      if(curr_disc != prev_disc) {
        discs[curr_disc] = [];
        prev_disc = curr_disc;
      }
      discs[curr_disc].push(data.result.tracks[i]);
    }
    
    for(var no in discs) {
      if(curr_disc > 1) {
        $('<h5></h5>').text(no).appendTo(this.ui);
      }
      self.resTbl[no] = self.createTable(no);
      self.resTbl[no].items = discs[no];
      self.resTbl[no].display();
    }
      
    self.ui.removeClass('loading');
    /* Invoke callback */
    self.options.onLoaded.call(self);
  };
  /* Ivokes highlight for all tables (discs) in album */
  this.highlightItem = function(id, cls) {
    for(var i in this.resTbl) {
      this.resTbl[i].highlightItem(id, cls);
    }
  };
  this.clearHighlight = function(cls) {
    for(var i in this.resTbl) {
      this.resTbl[i].clearHighlight(cls);
    }  
  };
};

// XXX: Should we use growl notifications?
var EventManager = {
  init: function() {
    $(document).bind("Status.state", EventManager.state);
    $(document).bind("Status.songinfo", EventManager.songinfo);
  },
  state: function() {
    if(Dogvibes.status.state == "playing") { return; }
    var user = "<b>Somebody</b> ";
    var msg;
    switch(Dogvibes.status.state) {
      case "stopped":
        msg = " stopped playback";
        break;
      case "paused":
        msg = "paused playback";
        break;
    } 
    $('#EventContainer').notify({ text: user + msg });
  },
  songinfo: function() {
    if(Dogvibes.status.state != "playing") { return; }
    var user = "<b>Somebody</b> "; 
    var pid = parseInt(Dogvibes.status.playlist_id, 10);
    var name = (pid === -1) ? "play queue" : Playlist.playlistNames[pid];
    name = name ? " from '"+name+"'" : "";
    var msg = " is playing '" + Dogvibes.status.title + "'";
    $('#EventContainer').notify({ text: user + msg + name });  
  }
};

// Control left or right view
var PageSwitch = {
  currentView: 'left',
  params: {
    left: {page: 'home', param: ''},
    right:{page: 'search', param: ''}
  },
  init: function() {
    $(document).bind("Page.search", function() {
      PageSwitch.scroll('right');
    });
    $(document).bind("Page.artist", function() {
      PageSwitch.scroll('right');
    });
    $(document).bind("Page.album", function() {
      PageSwitch.scroll('right');
    });        
    $(document).bind("Page.home", function() {   
      PageSwitch.scroll('left');
    });    
  },
  scroll: function(view) {
    if(PageSwitch.currentView == view) {
      return;
    }
    PageSwitch.currentView = view;
    var where = view == "left" ? 0 :'max';
    if(view == "right") {
      $('#Button-switch').addClass('social');      
    }
    else {
      $('#Button-switch').removeClass('social');    
    }
    $("#viewport").scrollTo(where, { axis: 'x', duration: 200, easing: 'swing' });  
  },
  toggle: function() {
    if(PageSwitch.currentView == "right") {
      PageSwitch.params.right.page = Dogbone.page.id;
      PageSwitch.params.right.param = Dogbone.page.param;
      window.location.hash = "#"+PageSwitch.params.left.page;
    }
    else {
      PageSwitch.params.left.page = Dogbone.page.id;
      PageSwitch.params.left.param = Dogbone.page.param;    
      window.location.hash = '#'+PageSwitch.params.right.page + '/' + PageSwitch.params.right.param;
    }
  }
};

// Displays popup and shade
var Popup = {
  _obj: false,
  init: function() {
    Popup._obj   = $("#popup");
    Popup._shade = $("#shade");
  },
  show: function() {
    if(Popup._obj) {
      Popup._obj.show();
    }
    if(Popup._shade) {
      Popup._shade.show();
    }    
  },
  hide: function() {
    if(Popup._obj) {
      Popup._obj.hide();
    }
    if(Popup._shade) {
      Popup._shade.hide();
    }    
  },
  message: function(text, loading) {
    if(Popup._obj) {
      Popup._obj.text(text);
      if(loading) {
        Popup._obj.addClass("loading");
      } else {
        Popup._obj.removeClass("loading");
      }
      Popup.show();
    }
  }
};

/***************************
 * Keybindings 
 ***************************/


/***************************
 * Startup 
 ***************************/
$(document).ready(function() {
  Dogvibes.getLoginInfo(Config.defaultServer,"checkLogin");
});

function checkLogin(json) {
  if(json.error == 5) {  
    window.location = "http://dogvib.es/authTwitter/" + Config.defaultUser;
  }
  else {
    startUp();  
  }
}

function startUp() {
  Popup.init();
  //TrackInfo.init();
  /* Init in correct order */
  Playqueue.init();
  Search.init();
  Artist.init();
  Activity.init();
  PageSwitch.init();
  //EventManager.init();
  //ScrollHandler.init();  
  ConnectionIndicator.init();
  User.init();
  Dogbone.init("pages"); 
  window.location.hash = "#home"; 
  /* Start server connection */
  Dogvibes.init(Config.defaultProtocol, Config.defaultServer, Config.defaultUser);

  //XXX: Move when user handling is in place
  $("#Dogvibes-info").text(Config.defaultUser);

  $("#Button-switch").click(function() {
    PageSwitch.toggle();
  });     
} 
