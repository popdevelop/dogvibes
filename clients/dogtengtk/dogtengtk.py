#!/usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk
import cjson
import urllib
import time
import pango

def updateGUI():
    global window
    global fix
    global label
    Base_URL = "http://192.168.0.16:8080/nystrom/amp/0/getAllTracksInQueue"
    WebSock = urllib.urlopen(Base_URL) # Opens a 'Socket' to URL
    WebHTML = WebSock.read() # Reads Contents of URL and saves to Variable
    WebSock.close() # Closes connection to url
    result = {}
    result = cjson.decode(WebHTML)
    var = 0
    
    window.remove(fix)
    fix = gtk.Fixed()
    window.add(fix)
    for tracks in result['result']:
        label = gtk.Label(str(var) + ".  " + tracks['title'])
        details = gtk.Label(tracks['artist']  + "  -   " + tracks['album'])
        if var==0:
            label.modify_font(pango.FontDescription("sans 40"))
            details.modify_font(pango.FontDescription("sans 14"))
        else:
            label.modify_font(pango.FontDescription("sans 20"))
            details.modify_font(pango.FontDescription("sans 14"))
        if var > 0:
            fix.put(label, 0,100 + var * 50)
            fix.put(details, 43,100 + var * 50 + 25)
        else:
            fix.put(label, 0,10)
            fix.put(details, 90,70)

        window.fullscreen()
        window.show_all()
        window.fullscreen()
        
        if var == 10:
            break
            
        var = var + 1
   
    return gtk.TRUE;

# Add a timeout to update the progress bar every 100 milliseconds or so
timeout_handler_id = gtk.timeout_add(1000, updateGUI)

# Start a timer to see how long the user runs this program
start = time.time()

# Create a new window
window = gtk.Window()
# Here we connect the "delete-event" event to a signal handler.
# This event occurs when we the user closes window,
# We connect it to gtk.main_quit, so it quits the main loop
# and the program terminates
window.connect("delete-event", gtk.main_quit)

fix = gtk.Fixed()

window.add(fix)

# Sets the border width of the window.
window.set_border_width(0)
window.fullscreen()

color = gtk.gdk.color_parse('#ffffff')
window.modify_bg(gtk.STATE_NORMAL, color)

# Show the window and the button
window.show_all()
# Run the main loop, to process events such a key presses
# and mouse movements.
gtk.main()
