from abc import abstractmethod, ABCMeta
import logging
import requests
import tmdbsimple as tmdb
from tvdb_api import Tvdb
import tempfile
import os

log = logging.getLogger(__name__)


class Tags(object):

    def __init__(self):
        self.title = ''
        self.date = ''
        self.cast = []
        self.writers = []
        self.directors = []
        self.producers = []
        self.genre = ''
        self.description = ''
        self.long_description = ''
        self.rating = ''
        self.poster_url = ''
        self.episode_number = 0
        self.season_number = 0
        self.network = ''
        self.show = ''
        self.season_total = 0


class FetchersFactory(object):
    TVFetchers = {}
    MovieFetchers = {}

    @classmethod
    def register(cls, fetcher):
        if fetcher.ftype == 'tv':
            cls.TVFetchers.update({fetcher.name: fetcher})
        elif fetcher.ftype == 'movie':
            cls.MovieFetchers.update({fetcher.name: fetcher})

    @classmethod
    def getfetcher(cls, fetcher: str, showid: int, id_type: str, language: str, season=None, episode=None):
        if season is not None:
            return cls.TVFetchers[fetcher](showid,
                                           id_type,
                                           season=season,
                                           episode=episode,
                                           language=language)
        else:
            return cls.MovieFetchers[fetcher](showid,
                                              id_type,
                                              season=None,
                                              episode=None,
                                              language=language)


class IFetcher(metaclass=ABCMeta):
    ftype = []
    source = ''

    def __init__(self, showid, id_type, season=None, episode=None, language='en', **kwargs):
        self.showid = showid
        self.id_type = id_type

        self.language = language
        self._fetcherid = None

        if season:
            self.season = season

        if episode:
            self.episode = episode

    @abstractmethod
    def gettags(self):
        pass

    def downloadArtwork(self, poster_url):
        posterfile = None
        r = requests.get(poster_url, stream=True)
        if r.status_code == 200:
            try:
                posterfile = os.path.join(tempfile.gettempdir(), f'poster-{self.fetcherid}.jpg')
                with open(posterfile, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
            except:
                pass

        return posterfile


class FetcherTmdb(IFetcher):
    ftype = ''
    name = 'tmdb'
    api_key = '45e408d2851e968e6e4d0353ce621c66'

    def __init__(self, showid, id_type, season=None, episode=None, language='en'):
        # Showinfo is a dict containing the name of the show, episode, season
        super(FetcherTmdb, self).__init__(showid, id_type, season=season, episode=episode, language=language)
        tmdb.API_KEY = FetcherTmdb.api_key
        self.tmdbconfig = tmdb.Configuration().info()
        self.definition = 'original'

        if self.id_type == 'tmdb_id':
            self._fetcherid = self.showid

        if self.id_type in ['imdb_id', 'freebase_mid', 'freebase_id', 'tvdb_id', 'tvrage_id']:
            find = tmdb.Find(self.showid)

            if self.__class__.ftype == 'tv':
                self._fetcherid = find.info(external_source=self.id_type)['tv_results'][0]['id']
            elif self.__class__.ftype == 'movie':
                self._fetcherid = find.info(external_source=self.id_type)['movie_results'][0]['id']

    @property
    def fetcherid(self):
        return self._fetcherid

    @abstractmethod
    def gettags(self):
        pass

    def _getposterpath(self, fetcher):
        images = fetcher.images(language=self.language)
        if len(images['posters']) == 0:
            images = fetcher.images()

        if images['posters']:
            posters = posterCollection()
            for img in images['posters']:
                posters.addPoster(
                    Poster(rating=img['vote_average'], ratingcount=img['vote_count'], bannerpath=img['file_path'])
                )

        poster = posters.topPoster()
        return '{base_url}{definition}{path}'.format(base_url=self.tmdbconfig['images']['base_url'],
                                                     definition=self.definition,
                                                     path=poster.bannerpath)


class FetcherTmdbTV(FetcherTmdb):
    ftype = 'tv'

    def __init__(self, showid, id_type, season=None, episode=None, language='en'):
        self._fetcherid = None
        super(FetcherTmdbTV, self).__init__(showid, id_type, season=season, episode=episode, language=language)

    def gettags(self):

        season = self.season
        episode = self.episode
        tags = Tags()
        episodedata = None
        showdata = None

        try:
            fetcher = tmdb.TV_Seasons(self.fetcherid, season)
            showdata = tmdb.TV(self.fetcherid).info(language=self.language)
            episodedata = tmdb.TV_Episodes(self.fetcherid, season, episode).info(language=self.language)
        except Exception:
            raise FetcherException

        if showdata:
            # Show parsers
            tags.season_total = showdata['number_of_seasons']
            tags.show = showdata['name']

            for net in showdata['networks']:
                if net['origin_country'] == showdata['origin_country'][0]:
                    tags.network = net['name']
                    break

            tags.genre = showdata['genres'][0]['name']

            # Season parsers
            tags.poster_url = self._getposterpath(fetcher)

            tags.episode_number = episode
            tags.season_number = season
            tags.title = episodedata['name']
            tags.date = episodedata['air_date']
            tags.ldescription = episodedata['overview']

            for member in episodedata['crew']:
                if member['job'] == 'Director':
                    tags.directors.append(member['name'])
                if member['job'] == 'Writer':
                    tags.writers.append(member['name'])

            return tags
        else:
            raise FetcherException


class FetcherTmdbMovie(FetcherTmdb):
    ftype = 'movie'

    def __init__(self, showid, id_type, season=None, episode=None, language='en'):
        super(FetcherTmdbMovie, self).__init__(showid, id_type, season=season, episode=episode, language=language)

    def gettags(self):
        try:
            movie = tmdb.Movies(self._fetcherid)
            moviedata = movie.info(language=self.language)

        except Exception:
            raise FetcherException

        tags = Tags()
        if moviedata:

            tags.title = moviedata['title']
            tags.description = moviedata['tagline']
            tags.long_description = moviedata['overview']
            tags.genre = movie.genres[0]['name']
            tags.poster_url = self._getposterpath(movie)

            for thedate in movie.release_dates()['results']:
                if thedate['iso_3166_1'].lower() == self.language:
                    tags.date = thedate['release_dates'][0]['release_date'][:10]

            if not tags.date:
                tags.date = moviedata['release_date']

            for member in movie.credits()['cast']:
                tags.cast.append(member['name'])
                if len(tags.cast) == 5:
                    break

            for member in movie.credits()['crew']:
                if member['job'] == "Director" and len(tags.directors) < 5:
                    tags.directors.append(member['name'])
                    continue
                if member['job'] == 'Producer' and len(tags.producers) < 5:
                    tags.producers.append(member['name'])
                    continue
                if member['job'] == 'Writer' or member['job'] == 'Author' and len(tags.writers) < 5:
                    tags.writers.append(member['name'])
                    continue
            return tags

        else:
            raise FetcherException


class FetcherTvdb(IFetcher):
    ftype = 'tv'
    name = 'tvdb'

    def __init__(self, showid, id_type, season=None, episode=None, language='en'):
        super(FetcherTvdb, self).__init__(showid, id_type, season=season, episode=episode, language=language)

        fetcher = Tvdb()
        if language in fetcher.config['valid_languages']:
            self.language = language
        else:
            self.language = 'en'
            log.error('Language %s not supported by tvdb, defaulting to English. Supported languages are {%s}',
                      language, fetcher.config['valid_languages'])

        self.fetcher = Tvdb(interactive=False, cache=True, banners=True, actors=True, forceConnect=True,
                            language=self.language)

        if self.id_type == 'tvdb_id':
            try:
                self._fetcherid = int(self.showid)
            except:
                raise FetcherException('id for the show should be an int')
        else:
            raise FetcherException('Tvdb only supports tvdb ids')

    @property
    def fetcherid(self):
        return self._fetcherid

    def gettags(self):
        season = self.season
        episode = self.episode

        show_data = self.fetcher[self.fetcherid]
        tags = Tags()

        data = show_data.data
        season_data = show_data[season]
        episode_data = season_data[episode]

        tags.show = data['seriesName']

        if data['genre']:
            tags.genre = data['genre'][0]

        tags.network = data['network']

        if data['rating']:
            tags.rating = data['rating']

        tags.seasons = len(season_data)
        tags.season_number = season

        tags.long_description = episode_data['overview']

        tags.episode_number = episode
        tags.title = episode_data['episodeName']

        banner_data = data['_banners']['season']['']
        for k in banner_data:
            if banner_data[k]['subKey'] == str(season) and banner_data[k]['_bannerpath']:
                tags.poster_url = banner_data[k]['_bannerpath']
                break

        if episode_data['writer']:
            for name in episode_data['writer']:
                if name != "":
                    tags.writers.append(name)

        for actor in data["_actors"]:
            if actor['name'] != "" and len(tags.cast) < 5:
                tags.cast.append(actor['name'])

        return tags


FetchersFactory.register(FetcherTvdb)

FetchersFactory.register(FetcherTmdbTV)

FetchersFactory.register(FetcherTmdbMovie)


class FetcherException(Exception):
    pass


class ArtworkException(FetcherException):
    pass


class Poster:
    # Simple source_container for all the poster parameters needed
    def __init__(self, rating=0, ratingcount=0, bannerpath=""):
        self.rating = rating
        self.bannerpath = bannerpath
        self.ratingcount = ratingcount


class posterCollection:
    def __init__(self):
        self.posters = []

    def topPoster(self):
        # Determines which poster has the highest rating, returns the Poster object
        top = None
        for poster in self.posters:
            if top is None:
                top = poster
            elif poster.rating > top.rating:
                top = poster
            elif poster.rating == top.rating and poster.ratingcount > top.ratingcount:
                top = poster
        return top

    def addPoster(self, inputPoster):
        self.posters.append(inputPoster)
