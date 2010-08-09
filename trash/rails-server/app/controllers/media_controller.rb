class MediaController < ApplicationController
  require "dbus"

  def play
    bus = DBus::SystemBus.instance
    service = bus.service("com.DogVibes.www")
    obj = service.object("/com/dogvibes/www")
    obj.introspect
    obj.default_iface = "com.DogVibes.www"
    obj.Play("gyllen", "bobdylan", params[:key])
  end

  def stop
    bus = DBus::SystemBus.instance
    service = bus.service("com.DogVibes.www")
    obj = service.object("/com/dogvibes/www")
    obj.introspect
    obj.default_iface = "com.DogVibes.www"
    obj.Stop("gyllen", "bobdylan")
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
      obj.Search("gyllen", "bobdylan", params[:q])[0].each { |song|
        unless(song.empty?)
          splitted = song.split(",")
          s = {:title => splitted[1], :artist => splitted[0], :key => splitted[2]}
          songs << s
        end
      }
    end

    render :json => songs.to_json
  end

end
