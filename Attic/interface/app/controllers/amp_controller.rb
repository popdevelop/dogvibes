class AmpController < ApplicationController
  require "dbus"

  def connectSpeaker
    get_amp(params[:id]).ConnectSpeaker(params[:nbr].to_i)
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def disconnectSpeaker
    get_amp(params[:id]).DisconnectSpeaker(params[:nbr].to_i)
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def getAllTracksInQueue
    tracks = get_amp(params[:id]).GetAllTracksInQueue()[0]
    render :json => {
      :error => 0,
      :tracks => tracks
    }.to_json, :callback => params[:callback]
  end

  def getStatus
    status = get_amp(params[:id]).GetStatus()[0]
    render :json => {
      :error => 0,
      :status => status
    }.to_json, :callback => params[:callback]
  end

  def getPlayedSeconds
    mseconds = get_amp(params[:id]).GetPlayedSeconds()[0]
    render :json => {
      :error => 0,
      :mseconds => mseconds
    }.to_json, :callback => params[:callback]
  end

  def getQueuePosition
    queue_position = get_amp(params[:id]).GetQueuePosition()[0]
    render :json => {
      :error => 0,
      :queue_position => queue_position
    }.to_json, :callback => params[:callback]
  end

  def nextTrack
    get_amp(params[:id]).NextTrack()
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def pause
    get_amp(params[:id]).Pause()
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def play
    get_amp(params[:id]).Play()
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def playTrack
    get_amp(params[:id]).PlayTrack(params[:nbr].to_i)
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def previousTrack
    get_amp(params[:id]).PreviousTrack()
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def queue
    get_amp(params[:id]).Queue(params[:uri])
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def removeFromQueue
    get_amp(params[:id]).RemoveFromQueue(params[:nbr].to_i)
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def seek
    get_amp(params[:id]).Seek(params[:mseconds].to_i)
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def setVolume
    get_amp(params[:id]).SetVolume(params[:level].to_f)
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  def stop
    get_amp(params[:id]).Stop()
    render :json => { :error => 0 }.to_json, :callback => params[:callback]
  end

  private

  def get_amp(id)
    bus = DBus::SystemBus.instance
    service = bus.service("com.Dogvibes")
    obj = service.object("/com/dogvibes/amp/0")
    obj.introspect
    obj.default_iface = "com.Dogvibes.Amp"
    return obj
  end

end
