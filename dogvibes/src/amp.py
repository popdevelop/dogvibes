

class Amp():
    def __init__(self, dogvibes, id):

    # API

    def API_connectSource(self, name, request):
        self.connect_source(name)
        request.finish(name)

    def API_disconnectSource(self, name, request):
        self.disconnect_source(name)
        request.finish(name)

    def API_connectSpeaker(self, nbr, request):
        self.connect_speaker(nbr)
        request.finish()

    def API_disconnectSpeaker(self, nbr, request):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            logging.warning ("disconnect speaker - speaker does not exist")

        speaker = self.dogvibes.speakers[nbr]

        if self.pipeline.get_by_name(speaker.name) != None:
            (pending, state, timeout) = self.pipeline.get_state()
            self.set_state(gst.STATE_NULL)
            rm = self.pipeline.get_by_name(speaker.name)
            self.pipeline.remove(rm)
            self.tee.unlink(rm)
            self.set_state(state)
        else:
            logging.warning ("disconnect speaker - speaker not found")
        request.finish()

    #def API_getAllTracksInQueue(self, request):
    #    # TODO: I don't know how to join these automatically
    #    tracks = []
    #    for entry in Playlist.objects.get(id=self.tmpqueue_id).entry_set.all().annotate(votes=Count('vote')):
    #        t = model_to_dict(entry.track)
    #        t["id"] = entry.id # use the unique id instead of track id
    #        t["votes"] = entry.votes # TODO: remove
    #        t["voters"] = [model_to_dict(v.user) for v in entry.vote_set.select_related()]
    #        tracks.append(t)
    #    request.finish(tracks)

    def API_getPlayedMilliSeconds(self, request):
        request.finish(self.get_played_milliseconds())

    def API_getStatus(self, request):
        request.finish(self.get_status())

    def API_next(self, request):
        self.next_track()
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_play(self, request):
        playlist = self.fetch_active_playlist()
        track = self.fetch_active_track()
        if track != None:
            self.set_state(gst.STATE_PLAYING)

        request.push({'state': self.get_state()})
        request.finish()

    def API_pause(self, request):
        self.set_state(gst.STATE_PAUSED)
        # FIXME we need to push the state paused to all clients
        # when play token lost, request == None
        if request != None:
            request.push({'state': self.get_state()})
            request.finish()

    def sort_playlist(self, playqueue):
        # Sort tracks in playqueue on number of votes and creation time
        if self.get_state() == "playing":
            playing = playqueue.entry_set.all()[0]
        for i, e in enumerate(playqueue.entry_set.annotate(num_votes=Count('vote')).order_by('-num_votes', 'created_at')):
            e.position = i
            e.save()
        # If we'e playing, move that track to the top again
        if self.get_state() == "playing":
            playing.insert_at(0)


    # TODO: addVote should exist in two modes, adding a URI from search and
    # voting for a specific entry in the playqueue.
    def API_vote(self, uri, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.dogvibes.create_track_from_uri(uri)
        playqueue = Playlist.objects.get(id=self.tmpqueue_id)

        # Get the first matching track if several with the same URI
        matching_tracks = playqueue.tracks.filter(uri=uri)
        if not matching_tracks:
            track = self.dogvibes.create_track_from_uri(uri)
            entry = Entry(track=track, playlist=playqueue)
        else:
            entry = matching_tracks[0].entry_set.get()

        if user.votes_left() < 1:
            logging.debug("No more votes left for %s" % user.username)
            request.finish(error = 3)
            return
        if user.already_voted(entry):
            logging.debug("%s already voted for track, ignoring" % user.username)
            request.finish(error = 3)
            return

        entry.save()

        if entry.position == 0 and self.get_state() == "playing":
            logging.debug("Can't vote for playing track")
            request.finish(error = 3)
            return

        # This is the actual voting
        Vote.objects.create(entry=entry, user=user)

        self.sort_playlist(playqueue)

        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_unvote(self, uri, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.dogvibes.create_track_from_uri(uri)
        playqueue = Playlist.objects.get(id=self.tmpqueue_id)

        # Get the first matching track if several with the same URI
        # NOTE: this will possibly choose the wrong track if several tracks
        # with the same URI are in the list
        matching_tracks = playqueue.tracks.filter(uri=uri)
        if not matching_tracks:
            track = self.dogvibes.create_track_from_uri(uri)
            entry = Entry.objects.create(track=track, playlist=playqueue)
        else:
            entry = matching_tracks[0].entry_set.get()

        if entry.position == 0 and self.get_state() == "playing":
            logging.debug("Can't remove vote for playing track")
            request.finish(error = 3)
            return

        # Remove vote
        entry.vote_set.filter(user=user).delete()
        self.sort_playlist(playqueue)

        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_queue(self, uri, request):
        playqueue = Playlist.objects.get(id=self.tmpqueue_id)
        tracks = self.dogvibes.create_tracks_from_uri(uri)
        [Entry.objects.create(playlist=playqueue, track=track) for track in tracks]

        self.playlist_version += 1
        self.needs_push_update = True
        request.finish()

    def API_removeTrack(self, track_id, request):
        track_id = int(track_id)

        # For now if we are trying to remove the existing playing track. Do nothing.
        if (track_id == self.active_playlist_id):
            logging.warning("Not allowed to remove playing track")
            request.finish(error = 3)
            return

        Entry.objects.get(id=track_id).delete()
        self.needs_push_update = True

        self.playlist_version += 1
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_removeTracks(self, track_ids, request):
        for track_id in track_ids.split(','):
            # don't crash on trailing comma
            if track_id != '':
                track_id = int(track_id)

                # For now if we are trying to remove the existing playing track. Do nothing.
                if (track_id == self.active_playlist_id):
                    logging.warning("Not allowed to remove playing track")
                    continue

                playlist = Playlist.get(self.tmpqueue_id)
                playlist.remove_playlist_tracks_id(track_id)
                self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_seek(self, mseconds, request):
        if self.src == None:
            request.finish(0)
        ns = int(mseconds) * 1000000
        logging.debug("Seek with time to ns=%d" %ns)
        self.pipeline.seek_simple (gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, ns)
        request.push({'duration': self.fetch_active_track().duration})
        request.finish()

    def API_setVolume(self, level, request):
        level = float(level)
        if (level > 1.0 or level < 0.0):
            raise DogError, 'Volume must be between 0.0 and 1.0'
        self.dogvibes.speakers[0].set_volume(level)
        request.push({'volume': self.dogvibes.speakers[0].get_volume()})
        request.finish()

    def API_stop(self, request):
        self.set_state(gst.STATE_NULL)
        request.push({'state': 'stopped'})
        request.finish()

    def API_getActivity(self, limit, request):
        activities = []
        for v in Vote.objects.all()[0:int(limit)]:
            a = model_to_dict(v.user)
            a.update(model_to_dict(v.entry.track))
            a["id"] = v.entry.id
            a["time"] = time.mktime(time.strptime(v.created_at.split(".")[0], "%Y-%m-%d %H:%M:%S"))
            activities.append(a)
        request.finish(activities)

    def API_getUserInfo(self, request):
        user, created = User.objects.get_or_create(username=request.user,
                                                   defaults={'avatar_url': request.avatar_url})
        ret = model_to_dict(user)
        ret["votes"] = user.votes_left()
        voted_tracks = []
        for vote in user.vote_set.all():
            track = model_to_dict(vote.entry.track)
            track["id"] = vote.entry.id
            voted_tracks.append(track)
        ret["voted_tracks"] = voted_tracks
        request.finish(ret)
