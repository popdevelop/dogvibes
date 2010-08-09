class DogvibesController < ApplicationController
  require "dbus"

  def search
    tracks = get_dogvibes.Search(params[:query])[0]
    render :json => {
      :error => 0,
      :tracks => tracks
    }.to_json, :callback => params[:callback]
  end

  private

  def get_dogvibes
    bus = DBus::SystemBus.instance
    service = bus.service("com.Dogvibes")
    obj = service.object("/com/dogvibes/dogvibes")
    obj.introspect
    obj.default_iface = "com.Dogvibes.Dogvibes"
    return obj
  end

end
