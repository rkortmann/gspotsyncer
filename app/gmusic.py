from app import app, cache
from gmusicapi import Mobileclient
from uuid import getnode as get_mac

class GoogleMusic():
	def __init__(self, user):
		self.user = user

	def __repr__(self):
		return "%s:%s" % (self.__class__.__name__,self.user._id)

	def connect(self, google_id, google_password):
		# set the credentials
		self.user.google_credentials = {
			'google_id' : google_id,
			'google_password' : google_password
		}

		# attempt a api verification
		if self.get_api():
			app.logger.info('Succesfully connected google account ID: ' + google_id)
			return self.user.save()
		else:
			flash('Unable to validate Google ID and password')
			self.disconnect()
			return False

	def disconnect(self):
		if hasattr(self.user, 'google_credentials'):
			del(self.user.google_credentials)
		return self.user.save()

	@cache.memoize(5 * 60)
	def search_songs(self, query):
		app.logger.info('Searching for song: ' + query)

		songs = []
		full_results = self.search(query)

		if full_results['song_hits']:
			songs = full_results['song_hits']

		return songs

	def search(self, query):
		api = self.get_api()
		results = []

		if api:
			results = api.search(query)

		return results

	def playlist_remove(self, playlist, delete_ids):
		app.logger.info('Removing ' + str(delete_ids) + ' from ' + str(playlist._id))

		# we need to translate trackIds into entry Ids
		# trackIds are used to add, but you need the specific
		# instance of this track in the playlist to delete
		entry_ids = []
		for track_id in delete_ids:
			for track_data in playlist.google_tracks:
				if track_data['trackId'] == track_id:
					entry_ids.append(track_data['id'])
					break

		app.logger.info('Translated into entriy IDs: ' + str(entry_ids))

		api = self.get_api()

		if api:
			return api.remove_entries_from_playlist(entry_ids)

		return False

	def playlist_add(self, playlist, insert_ids):
		app.logger.info('Adding ' + str(insert_ids) + ' from ' + str(playlist._id))

		playlist_id = playlist.google_playlist_data['id']

		if playlist_id and insert_ids:
			api = self.get_api()

			if api:
				return api.add_songs_to_playlist(playlist_id, insert_ids)

	@cache.memoize(30 * 60)
	def get_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_playlists()

		return playlists

	def get_playlists_select(self):
		formatted_playlists = []

		playlists = self.get_playlists()

		for playlist in playlists:
			formatted_playlists.append(( playlist['id'], playlist['name'] ))

		return formatted_playlists

	def get_full_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_user_playlist_contents()

		return playlists

	# @cache.memoize(30)
	def get_tracks(self, playlist=None):
		# api work handled in playlist function
		if playlist:
			playlists = self.get_full_playlists()

			for p in playlists:
				if p['id'] == playlist['id']:
					return p['tracks']

		return [];

	def get_api(self):
		if hasattr(self, 'api'):
			app.logger.info('Loaded cached Google API')
			return self.api

		api = Mobileclient()

		logged_in = api.login(self.user.google_credentials['google_id'], self.user.google_credentials['google_password'], api.FROM_MAC_ADDRESS)

		if logged_in:
			self.api = api
			return self.api
		return False