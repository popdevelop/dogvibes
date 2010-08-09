/*
 * Modules for handling playlists, searches, etc...
 */

var Config = {
  defaultUser: "sswc",
  defaultServer: "dogvib.es",
  defaultProtocol: ["ws", "http"], //Order to try protocols 
  resizeable: true,
  draggableOptions: {
    revert: 'invalid',
    distance: 10,
    scroll: false,
    revertDuration: 100, 
    helper: 'clone', 
    cursorAt: { left: 5 },
    appendTo: "#drag-dummy", 
    zIndex: 1000,
    addClasses: false,
    start: function() { $(this).click(); }
  },
  sortableOptions: {
    revert: 100,
    distance: 10,
    scroll: false, 
    helper: 'clone', 
    appendTo: "#drag-dummy", 
    zIndex: 1000,
    addClasses: false
  }  
};


/* TODO: remove when all dependencies are solved */
var UI = {
  titlebar: "#titlebar",
  navigation: "#navigation",
  trackinfo: "#trackinfo",
  currentsong: "#currentsong"
};

/* TODO: Find out a good way to handle titlebar */
var Titlebar = {
  set: function(text) {
    $(UI.titlebar).empty();
    $(UI.titlebar).append($("<li class='selected'>"+text+"</li>"));
  }
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

/******************
 * Helper classes
 ******************/
var ResultTable = function(config) {
  var self = this;
  /* Default configuration */
  this.options = {
    name: "Table",
    idTag: "id",
    highlightClass: "playing",
    sortable: false,
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

  if(self.options.sortable) {
    $(self.ui.content).tablesorter();
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


var NavList = {
  /* Store all sections globally */
  sections: Array(),
  /* Section object */  
  Section: function(container, type) {
    this.ul = $(container);
    this.ul.addClass(type);
    NavList.sections.push(this);
    this.items = Array();
    $(UI.navigation).append(this.ul);    
    this.addItem = function(id, item) {
      this.items[id] = $(item);
      this.ul.append(this.items[id]);
    };
    this.selectItem= function(id) {
      $(NavList.sections).each(function(i ,el) {
        el.deselect();
      });
      if(typeof(this.items) != "undefined" && id in this.items) {
        this.items[id].addClass('selected');
      }
    };
    this.deselect = function() {
      for(var i in this.items) {
        this.items[i].removeClass('selected');
      }
    };
    this.empty = function() {
      this.items = Array();
      this.ul.empty();
    };
  }
};


/**************************
 * Modules 
 **************************/

var Main = {
  ui: {
    page   : "#playqueue",
    section: "#Main-section"
  },
  init: function() {
    /* Bug in jQuery: you can't have same function attached to multiple events! */    
    Main.ui.list = new NavList.Section(Main.ui.section, '');
    Main.ui.list.addItem("home", $("<li class='home'><a href='#home'>Home</a><li>"));
    $(document).bind("Page.home", Main.setHome);
    Main.ui.playqueue = $("<li class='playqueue'><a href='#playqueue'>Play queue</a></li>");
    Main.ui.playqueue.droppable({
      hoverClass: 'drophover',
      tolerance: 'pointer',
      drop: function(event, ui) {
        var uri = ui.draggable.data("uri");
        if(uri) {
          Dogvibes.queue(uri);
          return;
        }
        /* try album_uri aswell */
        uri = ui.draggable.data("album_uri");
        if(uri) {
          Dogvibes.queueAlbum(uri);
        }        
      }
    });
    Main.ui.list.addItem("playqueue", Main.ui.playqueue);
    $(document).bind("Page.playqueue", Main.setQueue); 
  },
  setQueue: function() {
    Titlebar.set("Play queue");
    Main.ui.list.selectItem(Dogbone.page.id);
    Playqueue.fetch();
  },
  setHome: function() {
    Titlebar.set("Home");
    Main.ui.list.selectItem(Dogbone.page.id);
  }  
};

var Playqueue = {
  ui: {
    page: "#playqueue",
    info: "#Playqueue-info"
  },
  table: false,
  hash: false,
  init: function() {
    $(Playqueue.ui.info).text('Play queue not available when offline').hide();
    /* Create a table for our tracks */
    Playqueue.table = new ResultTable(
    {
      name: 'Playqueue', 
      dblclick: function() {
        var id = $(this).data('id');
        Dogvibes.playTrack(id, "-1");
      },
      /* Add a remove-icon  */
      callbacks: {
        space: function(element) {        
          $('<span> remove </span>')
            .data('id', element.id)
            .data('nbr', element.nbr)
            .attr("title", "remove track(s) from playqueue")
            .click(function(e) {
              var id = $(this).data('id');
              var nbr = $(this).data('nbr');
              /* if clicked item is in selected range, remove entire range */
              if( Playqueue.table.selectedItems.indexOf(nbr) != -1 ) {
                id = [];
                $(Playqueue.table.selectedItems).each(function(i, el) {
                  id.push(Playqueue.table.data[el].data('id'));
                  $("#Playqueue-item-nbr-"+el).remove();
                });
                $(id).get().join(',');
              } else {
                $("#Playqueue-item-nbr-"+nbr).remove();
              }
              Dogvibes.removeTrack(id);              
              e.preventDefault();
              return false;
          }).appendTo(element);
        }
      }
    });
    
    $(document).bind("Status.playlistchange", function() { Playqueue.fetch(); });
    $(document).bind("Status.state", function() { Playqueue.set(); });
    $(document).bind("Status.playlist", function() { Playqueue.set(); });
    $(document).bind("Server.connected", function() {
      $(Playqueue.ui.info).hide();
      Playqueue.fetch();      
    });
    $(document).bind("Server.error", function() {
      $(Playqueue.ui.info).show();
      Playqueue.table.empty();      
    });    
  },  
  fetch: function() {
    if(Dogbone.page.id != "playqueue") { return; }
    if(Dogvibes.server.connected) { 
      Playqueue.hash = Dogvibes.status.playlistversion;
      Dogvibes.getAllTracksInQueue("Playqueue.update");
    }
  },
  update: function(json) { 
    if(json.error !== 0) {
      return;
    }
    Playqueue.table.items = json.result;
    Playqueue.table.display();
    Playqueue.set();
    /* Make draggable/sortable. TODO: move into ResultTable */
    $(function() {
      $("tr", Playqueue.table.ui.items).draggable(Config.draggableOptions);
    });     
  },
  set: function() {
    $("li.playqueue").removeClass('playing paused');
    Playqueue.table.clearHighlight('playing paused');      
    if(Dogvibes.status.playlist_id !== -1) { return; }
    cls = Dogvibes.status.state;
    if(Dogvibes.status.state == "playing" ||
       Dogvibes.status.state == "paused") {
      $("li.playqueue").addClass(cls); 
      Playqueue.table.highlightItem(Dogvibes.status.index, cls);      
    }
  }
};

var PlayControl = {
  ui: {
    controls: "#PlayControl",
    prevBtn : "#pb-prev",
    playBtn : "#pb-play",
    nextBtn : "#pb-next",
    volume  : "#Volume-slider",
    seek    : "#TimeInfo-slider",
    elapsed : "#TimeInfo-elapsed",
    duration: "#TimeInfo-duration"
  },
  volSliding: false,
  seekSliding: false,
  updateTimer: true,
  init: function() {
    $(document).bind("Status.state", PlayControl.set);
    $(document).bind("Status.volume", PlayControl.setVolume);
    $(document).bind("Status.elapsed", function() {
      PlayControl.setTime({result: Dogvibes.status.elapsedmseconds});
    });
    
    $(PlayControl.ui.volume).slider( {
      start: function(e, ui) { PlayControl.volSliding = true; },
      stop: function(e, ui) { PlayControl.volSliding = false; },
      change: function(event, ui) { 
        Dogvibes.setVolume(ui.value/100);
      }
    });
    
    $(PlayControl.ui.seek).slider( {
      start: function(e, ui) { PlayControl.seekSliding = true; },
      stop: function(e, ui) { PlayControl.seekSliding = false; },
      change: function(event, ui) { 
        Dogvibes.seek(Math.round((ui.value*Dogvibes.status.duration)/100));
      }
    });    
    
    $(PlayControl.ui.nextBtn).click(function() {
      Dogvibes.next();
      this.blur();
    });

    $(PlayControl.ui.playBtn).click(function() {
      PlayControl.toggle();
      this.blur();      
    });
    
    $(PlayControl.ui.prevBtn).click(function() {
      Dogvibes.prev();
      this.blur();      
    });
  },
  set: function() {
    $(PlayControl.ui.controls).removeClass();
    $(PlayControl.ui.controls).addClass(Dogvibes.status.state);
    if(Dogvibes.status.state == "stopped") {
      PlayControl.setTime({result: 0});
      $(PlayControl.ui.seek).slider( "option", "disabled", true );
    } else {
      $(PlayControl.ui.seek).slider( "option", "disabled", false );
    }
    //$(PlayControl.ui.duration).text(Dogvibes.status.duration.msec2time());    
  },
  toggle: function() {
    if(Dogvibes.status.state == "playing") {
      Dogvibes.pause();
    } else {
      Dogvibes.play();
    }
    PlayControl.set();
  },
  setVolume: function() {
    if(PlayControl.volSliding) { return; }
    $(PlayControl.ui.volume).slider('option', 'value', Dogvibes.status.volume*100);  
  },
  setTime: function(elapsed) {
    //$(PlayControl.ui.elapsed).text(Dogvibes.status.elapsedmseconds.msec2time());
    var newVal = (typeof(Dogvibes.status.duration) == 'undefined') ? 0 : (elapsed.result/Dogvibes.status.duration)*100;
    if(PlayControl.seekSliding) { return; }
    $(PlayControl.ui.seek).slider('option', 'value', newVal); 
    /* Fetch another time update */
    if(PlayControl.updateTimer && 
       Dogvibes.server.connected &&
       Dogvibes.status.state != 'stopped') {
      clearTimeout(PlayControl.updateTimer);
      PlayControl.updateTimer = setTimeout(function() {
        Dogvibes.getPlayedMilliSecs("PlayControl.setTime");
      }, 500);      
    }
  }  
};

var ConnectionIndicator = {
  ui: {
    icon: "#ConnectionIndicator-icon"
  },
  icon: false,
  init: function() {
    ConnectionIndicator.icon = $(ConnectionIndicator.ui.icon);
    if(ConnectionIndicator.icon) {
      $(document).bind("Server.connecting", function() {
        ConnectionIndicator.icon.removeClass();
        //ConnectionIndicator.icon.addClass("connecting");
      });
      $(document).bind("Server.error", function() {
        ConnectionIndicator.icon.removeClass();
        ConnectionIndicator.icon.addClass("error");
      });
      $(document).bind("Server.connected", function() {
        ConnectionIndicator.icon.removeClass();
        ConnectionIndicator.icon.addClass("connected");
      });       
    }
  }
};

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

var Playlist = {
  ui: {
    section : "#Playlist-section",
    newPlist: "#Newlist-section",
    info : "#Playlist-info"
  },
  table: false,
  selectedList: "",
  playlistNames: {},
  init: function() {
    $(Playlist.ui.info).text('Playlist not available when offline').hide();
    Playlist.ui.list =    new NavList.Section(Playlist.ui.section, 'playlists');
    Playlist.ui.newList = new NavList.Section(Playlist.ui.newPlist, 'last');
    Playlist.ui.newBtn  = $("<li class='newlist'><a>New playlist</a></li>");
    Playlist.ui.newBtn.click(function() {
      var name = prompt("Enter new playlist name");
      if (name != null && name != "") {
        Dogvibes.createPlaylist(name, "Playlist.fetchAll");
      }
    });
    Playlist.ui.newList.addItem('newlist', Playlist.ui.newBtn);
    
    /* Create a table for the tracks */
    Playlist.table = new ResultTable(
    {
      name: 'Playlist',
      highlightClass: "playing",
      /* Dblclick event */
      dblclick: function() {
        var index = $(this).data('id');
        Playlist.playItem(index);
      },
      /* Add a remove-icon  */
      callbacks: {
        space: function(element) {        
          $('<span> remove </span>')
            .data('id', element.id)
            .data('nbr', element.nbr)
            .attr("title", "remove track(s) from playlist")
            .click(function(e) {
              var id = $(this).data("id");
              var nbr =$(this).data("nbr"); 
              var pid = Playlist.selectedList;
              /* if clicked item is in selected range, remove entire range */
              if( Playlist.table.selectedItems.indexOf(nbr) != -1 ) {
                id = [];
                $(Playlist.table.selectedItems).each(function(i, el) {
                  id.push(Playlist.table.data[el].data('id'));
                  $("#Playlist-item-nbr-"+el).remove();
                });
                id = $(id).get().join(',');

              } else {
                $("#Playlist-item-nbr-"+nbr).remove();
              }
              Dogvibes.removeFromPlaylist(id, pid);
              e.preventDefault();
              return false;
          }).appendTo(element);
        }
      }
    });

    /* Setup events */
    $(document).bind("Page.playlist", Playlist.setPage);
    $(document).bind("Status.playlistchange", function() { Playlist.setPage(); Playlist.fetchAll(); });   
    $(document).bind("Server.connected", function() { $(Playlist.ui.info).hide(); Playlist.fetchAll(); });
    $(document).bind("Server.error", function() {
      $(Playlist.ui.info).show();
      Playlist.table.empty();      
    });
    $(document).bind("Status.state", function() { Playlist.set(); });    
    $(document).bind("Status.songinfo", function() { Playlist.set(); });    
    $(document).bind("Status.playlist", function() { Playlist.set(); });       
    /* Handle sorts */
    $(Playlist.table.ui.items).bind("sortupdate", function(event, ui) {
      var items = $(this).sortable('toArray');
      var trackPos =$(ui.item).data("nbr"); 
      var trackID = $(ui.item).data("id");
      var position;
      for(var i = 0; i < items.length; i++) {
        if(items[i] == "Playlist-item-nbr-"+trackPos) {
          position = i;
          break;
        }
      }
      Dogvibes.move(Playlist.selectedList, trackID, (position+1), "Playlist.setPage");
    });               
  },
  setPage: function() {
    if(Dogbone.page.id != "playlist") { return; }
    Playlist.ui.list.selectItem(Dogbone.page.param);
    Titlebar.set("Playlist");
    
    if(Dogvibes.server.connected) {
      /* Save which list that is selected */
      Playlist.selectedList = Dogbone.page.param;
      /* Load new items */
      Dogvibes.getAllTracksInPlaylist(Playlist.selectedList, "Playlist.handleResponse");
    }
  },
  fetchAll: function() {
    Dogvibes.getAllPlaylists("Playlist.update");
  },
  update: function(json) {
    Playlist.ui.list.empty();
    if(json.error !== 0) {
      alert("Couldn't get playlists");
      return;
    }
    Playlist.playlistNames = {};
    $(json.result).each(function(i, el) {
      /* Save names */
      Playlist.playlistNames[el.id] = el.name;
      /* Create list item */
      var item = 
      $('<li></li>')
      .attr("id", "Playlist-"+el.id)
      .append(
        $('<a></a>')
        .attr("href", "#playlist/"+el.id)
        .text(el.name)
        .click(function() {
          $(this).blur();
        })
      );
      /* Make droppable */
      item.droppable({
        hoverClass: 'drophover',
        tolerance: 'pointer',
        drop: function(event, ui) {
          var id = $(this).attr("id").removePrefix("Playlist-");
          var uri = ui.draggable.data("uri");
          if(uri) {
            Dogvibes.addToPlaylist(id, uri);
            return;
          }
          /* try album_uri aswell */
          uri = ui.draggable.data("album_uri");
          if(uri) {
            Dogvibes.addAlbumToPlaylist(id, uri);
          }
        }
      });
      /* Remove-button */
      $('<span> remove </span>')
      .data("id", el.id)
      .attr("title", "remove this playlist")
      .click(function() {
        if(confirm("Do you want to remove this playlist?")) {
          var id = $(this).data("id");
          Dogvibes.removePlaylist(id, "Playlist.fetchAll");
          /* FIXME: solve this nicer */
          if(id == Playlist.selectedList) {
            location.hash = "#home";
          }
        }
      }).appendTo(item);
      /* Rename-button */
      $('<em> rename </em>')
      .data("id", el.id)
      .attr("title", "rename this playlist")
      .click(function() {
        var id = $(this).data('id');
        var newname = prompt("Enter new playlist name", Playlist.playlistNames[id]);
        if(newname != '' && newname != null) {
          Dogvibes.renamePlaylist(id, newname);
        }
      }).appendTo(item);      
      Playlist.ui.list.addItem(el.id, item);
    });
    /* Update info */
    Playlist.setPage();
    Playlist.set();
  },

  handleResponse: function(json) {
    if(json.error !== 0) {
      alert("Couldn't get playlist");
      return;
    }
    Playlist.table.items = json.result;
    Playlist.table.display();    
    Playlist.set();
    $(function() {
      $(Playlist.table.ui.items).sortable(Config.sortableOptions);
    });     
  },
  playItem: function(id) {
    var nbr = parseInt(id, 10);
    if(!isNaN(nbr)) {
      Dogvibes.playTrack(id, Playlist.selectedList);
    }
  },
  set: function() {  
    Playlist.table.clearHighlight('playing paused');
    $('li', Playlist.ui.list.ul).removeClass('playing paused');
    cls = Dogvibes.status.state;
    if(Dogvibes.status.state == "playing" ||
       Dogvibes.status.state == "paused") {
      $("#Playlist-"+Dogvibes.status.playlist_id).addClass(cls);
      //Playlist.table.options.highlightClass = cls;
      if(Dogvibes.status.playlist_id == Playlist.selectedList) {    
        Playlist.table.highlightItem(Dogvibes.status.index, cls);
      }
    } 
  } 
};

var Search = {
  ui: {
    form:    "#Search-form",
    input:   "#Search-input",
    section: "#Search-section",
    page   : "#search",
    info   : "#Search-info"
  },
  searches: [],
  param: "",
  table: false,
  init: function() {
    /* Init search navigation section */
    Search.ui.list = new NavList.Section(Search.ui.section,'search');
    $(document).bind("Page.search", Search.setPage);
    
    $(document).bind("Status.songinfo", Search.set);
    $(document).bind("Status.state", function() { Search.set(); });
    
    /* Handle offline/online */
    $(document).bind("Server.error", function() {
      $(Search.ui.page).removeClass();
      $(Search.table.ui.content).hide();
      $(Search.ui.info).text('Search not available when offline').show();
    });
    $(document).bind("Server.connected", function() {
      $(Search.ui.info).hide();
      $(Search.table.ui.content).show();    
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
    
    /* Create result table */
    Search.table = new ResultTable(
    {
      idTag: "uri",
      name: "Search",
      sortable: true,
      dblclick: function() {
        var uri = $(this).data('uri');
        Dogvibes.queueAndPlay(uri);    
      },
      callbacks: {
        popularity: function(element) {
          var value = element.text();
          var bar = $('<div></div>').css('width', (value*60)+"px");
          element.contents().wrap(bar);
        }
      }
    });
  
    /* Load searches from cookie */
    var temp;
    for(var i = 0; i < 6; i++){
      if((temp = getCookie("Dogvibes.search" + i)) != "") {
        Search.searches[i] = temp;
      }
    }
    Search.draw();
  },
  setPage: function() {
    if(Dogbone.page.id != "search") { return; }
    /* See if search parameter has changed. If so, reload */
    if(Dogvibes.server.connected &&
       Dogbone.page.param != Search.param) {
      Search.param = Dogbone.page.param;
      var keyword = unescape(Search.param);
      Search.searches.push(keyword);
      Search.table.empty();
      $(Search.ui.page).addClass("loading");
      Search.addSearch(keyword);
      $(Search.ui.info).hide();
      Dogvibes.search(Search.param, "Search.handleResponse");
    }
    Search.setTitle();    
    Search.ui.list.selectItem(Dogbone.page.param);
  },
  addSearch: function(keyword) {
    var tempArray = Array();
    tempArray.unshift($.trim(keyword));
    $.each(Search.searches, function(i, entry){
      if($.trim(keyword) != entry){
        tempArray.push(entry);
      }
    });
    if(tempArray.length > 6){
      tempArray.pop();
    }
    Search.searches = tempArray;
    for(var i = 0; i < tempArray.length; i++) {
      setCookie("Dogvibes.search" + i, tempArray[i]);
    }
    Search.draw();  
  },
  draw: function() {
    Search.ui.list.empty();
    $(Search.searches).each(function(i, el) {
      Search.ui.list.addItem(el,"<li class='"+el+"'><a href='#search/"+el+"'>"+el+"</a></li>");
    });
  },
  setTitle: function() {
    $(UI.titlebar).empty();
    $(UI.titlebar).append($("<li class='selected'>Search</li>"));
    $(UI.titlebar).append($("<li class='keyword'>"+Search.param+"</li>"));    
  },
  doSearch: function(keyword) {
    window.location.hash = "#search/"+keyword;
  },
 
  handleResponse: function(json) {
    $(Search.ui.page).removeClass("loading");  
    if(json.error !== 0) {
      alert("Search error!");
      return;
    }
    /* Any results? */
    if(json.result.length === 0) {
      $(Search.ui.info).text('Sorry, no matches for "'+Dogbone.page.param+'"').show();
    }
    Search.table.items = json.result;
    Search.table.display();
    $(function() {
      $(Search.table.ui.items + " tr").draggable(Config.draggableOptions);
    }); 
    Search.set();   
  },
  set: function() {
    /* Set playing if any song matches */
    var cls = false;
    switch(Dogvibes.status.state) {
      case "playing":
      case "paused":
        cls = Dogvibes.status.state;
        break;
    }
    $("tr", Search.table.ui.items).removeClass('playing paused');
    if(!cls) { return; }
    
    Search.table.highlightItem(Dogvibes.status.uri, cls);
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
      Titlebar.set("Album");    
      var album = Dogbone.page.param;
      $("#album").empty();
      Dogvibes.getAlbum(album, "Artist.setAlbum");
    }
    else if(Dogbone.page.id == "artist" && Artist.currentArtist != Dogbone.page.param){
      Titlebar.set("Artist");
      Artist.currentArtist = Dogbone.page.param;
      /* Reset and fetch new data */
      Artist.albums.items = [];
      Artist.albums.data = {};
      $('#artist').empty().append('<h2>'+Dogbone.page.param+'</h2>');
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
        $('<h3></h3>').text("Appears on").appendTo('#artist');
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
    /* FIXME: this could perhaps be more efficient */
      /* Which class should apply? */
    var cls = false;
    switch(Dogvibes.status.state) {
      case "playing":
      case "paused":
        cls = Dogvibes.status.state;
        break;
    }
    
    /* First set single album-view */
    if(Artist.album) {     
      /* Remove previous classes */
      Artist.album.clearHighlight("playing paused");
    
      if(cls) { 
        /* Set new class */
        Artist.album.highlightItem(Dogvibes.status.uri, cls);
      }
    }
    
    /* Now, the album listing for artist */
    var noAlbums = Artist.albums.items.length;
    if(noAlbums > 0) {
      for(var i = 0; i < noAlbums; i++) {
        var a = Artist.albums.items[i];
        /* Remove current */
        a.clearHighlight("playing paused");
        if(cls) {
          /* Set new class */
          a.highlightItem(Dogvibes.status.uri, cls);
        }       
      }
    }
  },
  /* Things to do when an album has loaded */
  albumCallback: function() {
    var cls = false;
    switch(Dogvibes.status.state) {
      case "playing":
      case "paused":
        cls = Dogvibes.status.state;
        break;
    }
    if(cls) {
      this.highlightItem(Dogvibes.status.uri, cls);
    }
  }
};

var ScrollHandler = {
  /* Different handlers for pages */
  handlers: {
    artist: Artist.displayMore
  },
  container: false,
  init: function() {
    /* Invoke action on scroll bottom */
    $("#content").scroll(function() { ScrollHandler.checkScroll() });  
    ScrollHandler.container = $("#content");
  },
  checkScroll: function() {
    if(Dogbone.page.id in ScrollHandler.handlers) {
      if(ScrollHandler.container[0].scrollHeight - ScrollHandler.container.height() - ScrollHandler.container.scrollTop() <= 0) {
        ScrollHandler.handlers[Dogbone.page.id]();
      }
    }  
  }
}

/*
 * Class for displaying/fetching an album from uri
 */
var AlbumEntry = function(entry, options) {
  var self = this;
  this.options = {
    albumLink: true,
    onLoaded: $.noop
  }
  $.extend(this.options, options);
  this.tableName = entry.uri.replace(/:/g, '_');
  this.tableName = this.tableName.replace(/\//g, '')
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
    .draggable(Config.draggableOptions)
    .dblclick(function() {
      uri = $(this).data("album_uri");
      if(uri) {
        Dogvibes.queueAlbum(uri);
      } 
    })
    .appendTo(art);
    
  /* Clickable album? */
  if(this.options.albumLink) {
    var titlelink = 
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
        Dogvibes.queueAndPlay(uri);    
      },
      callbacks: {
        track_number: function(element) {
          element.addClass('trackNo');
        }
      }
    });    
  },
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
      $(function() {
        $("tr", self.resTbl[no].ui.items).draggable(Config.draggableOptions);
      });
    }
      
    self.ui.removeClass('loading');
    /* Invoke callback */
    self.options.onLoaded.call(self);
  },
  /* Ivokes highlight for all tables (discs) in album */
  this.highlightItem = function(id, cls) {
    for(var i in this.resTbl) {
      this.resTbl[i].highlightItem(id, cls)
    }
  },
  this.clearHighlight = function(cls) {
    for(var i in this.resTbl) {
      this.resTbl[i].clearHighlight(cls)
    }  
  }
};

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
    var name = name ? " from '"+name+"'" : "";
    msg = " is playing '" + Dogvibes.status.title + "'";
    $('#EventContainer').notify({ text: user + msg + name });  
  }
};

/***************************
 * Keybindings 
 ***************************/
 
/* CTRL+s for searching */ 
$(document).bind("keyup", "ctrl+s", function() {
  $(Search.ui.input).focus();
});

$(document).bind("keyup", "ctrl+p", function() {
  PlayControl.toggle();
});

$(document).dblclick(function() {
  var sel;
  if(document.selection && document.selection.empty){
    document.selection.empty() ;
  } else if(window.getSelection) {
    sel=window.getSelection();
  }
  if(sel && sel.removeAllRanges) {
    sel.removeAllRanges();
  }
});

/***************************
 * Startup 
 ***************************/
$(document).ready(function() {
  
  /* Zebra stripes for all tables */
  $.tablesorter.defaults.widgets = ['zebra'];

  Dogbone.init("content");
  ConnectionIndicator.init();
  PlayControl.init();
  TrackInfo.init();
  /* Init in correct order */
  Playqueue.init();
  Main.init();
  Search.init();
  Playlist.init();
  Artist.init();
  EventManager.init();
  ScrollHandler.init();
  /* Start server connection */
  Dogvibes.init(Config.defaultProtocol, Config.defaultServer, Config.defaultUser);
  
  /****************************************
   * Misc. behaviour. Application specific
   ****************************************/
   
  /* Display username */
  $('#userinfo').text(Config.defaultUser);
   
  /* FIXME:  */
  $(UI.trackinfo).click(function() {
    $(UI.navigation).toggleClass('fullHeight');
    $(UI.currentsong).toggleClass('minimized');
  });
  
  /* Splitter */
  $("#separator").draggable( {
    containment: [150, 0, 300, 0],
    axis: 'x',
    drag: PanelSplit.drag
  });
  
}); 

var PanelSplit = {
  left: 180,
  drag: function(event, ui) {
    PanelSplit.set(ui.position.left);
  },
  set: function(left) {
    $(".resizable-right").css("width", left+"px");
    $(".resizable-left").css("left", left+"px");
    $(".resizable-top").each(function(i, el) {
      var height = $(el).height();
      $(el).height(height + (left - PanelSplit.left));
    });    
    $(".resizable-bottom").each(function(i, el) {
      var height = $(el).css("bottom");
      height = parseInt(height.substring(0, height.indexOf("px")), 10);
      $(el).css("bottom", (height + (left - PanelSplit.left)) + "px");
    });
    PanelSplit.left = left;
  }
};
