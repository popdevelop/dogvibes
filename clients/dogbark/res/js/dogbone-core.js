/*
 * Dogbone core functionality for handling navigation
 */

window.Dogbone = {
  defaultPage: "home",
  pageRoot: null,
  pages: [],
  currentHash: "",
  page: { id: "", param: false},
  init: function(root) {
    var rootObj = document.getElementById(root);
    if(rootObj) {
      Dogbone.pageRoot = rootObj;
      Dogbone.findPages();
      $(Dogbone.pages).each(function(id,el) { Dogbone.hidePage(el); });
      if(location.hash.length === 0 &&
         Dogbone.defaultPage.length > 0) {
        location.hash = "#"+Dogbone.defaultPage;
      }
      setInterval(Dogbone.checkLocation, 300);
    }
  },
  /* Go through children of root object and assign as pages */
  findPages: function() {
    $(Dogbone.pageRoot).children().each(function(i, el) {
      if(el.id) {
        Dogbone.pages.push(el.id);
      }
    });
  },
  showPage: function(pageID, param) {
    var pageObj = $("#"+pageID);
    if(pageObj && ($.inArray(pageID, Dogbone.pages) !== -1)) {
      Dogbone.hidePage(Dogbone.page.id);
      pageObj.show();      
    }
    Dogbone.page.id    = pageID;
    Dogbone.page.param = param;    
    $(document).trigger("Page."+pageID);
  },
  hidePage: function(pageID) {
    if(pageID) {
      $('#'+pageID).hide();
    }
  },
  /* Continously monitor location */
  checkLocation: function() {
    if(location.hash != Dogbone.currentHash) {
      var hash = location.hash.substr(1);
      var ppos, pageId, param;

      ppos = hash.indexOf("/");
      if(ppos >= 0) {
        pageId = hash.substring(0, ppos);
        param  = hash.substring(ppos+1);
      } else {
        pageId = hash;
        param  = "";
      }
      Dogbone.currentHash = location.hash;
      Dogbone.showPage(pageId, param);
    }    
  }
};
