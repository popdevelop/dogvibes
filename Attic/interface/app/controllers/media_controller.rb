class MediaController < ApplicationController
  require "dbus"

  def play
    puts params.inspect
    #bus = DBus::SystemBus.instance
    #service = bus.service("com.DogVibes.www")
    #obj = service.object("/com/dogvibes/www")
    #obj.introspect
    #obj.default_iface = "com.DogVibes.www"
    #obj.Play(params[:input], params[:output], params[:key])
  end

  def stop
    bus = DBus::SystemBus.instance
    service = bus.service("com.DogVibes.www")
    obj = service.object("/com/dogvibes/www")
    obj.introspect
    obj.default_iface = "com.DogVibes.www"
    obj.Stop()
  end

  def pause
  end

  def search
    bus = DBus::SystemBus.instance

    service = bus.service("com.DogVibes.www")
    obj = service.object("/com/dogvibes/www")

    songs = []

    obj.introspect

    if obj.has_iface? "com.DogVibes.www"
      obj.default_iface = "com.DogVibes.www"
      obj.Search("", "", params[:q])[0].each { |song|
        unless(song.empty?)
          splitted = song.split(",")
          s = {:title => splitted[1], :artist => splitted[0], :key => splitted[2]}
          songs << s
        end
      }
    end

    songs = [
             { :title => 'Wonderwall', :artist => 'Oasis', :key => "C:/Music/Oasis.mp3" },
             { :title => 'One', :artist => 'Metallica', :key => "C:/Music/Metallica.mp3" }
            ]

    # return in JSONP (JSON with padding) format
    render :json => params[:callback] + '(' + songs.to_json + ')'

  end

end
