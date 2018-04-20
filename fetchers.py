import os
import tempfile
from abc import abstractmethod, ABCMeta

import requests
import tmdbsimple as tmdb
from requests.compat import urljoin
from tvdb_api import Tvdb


class Info(object):
    def __init__(self):
        self.title = ''
        self.date = None
        self.cast = []
        self.writers = []
        self.director = []
        self.genre = ''
        self.description = ''
        self.ldescription = ''
        self.rating = ''
        self.artworkpath = ''

    def shortendescription(self):
        pass


class MovieInfo(Info):
    def __init__(self):
        super(MovieInfo, self).__init__()
        self.producer = []


class TvInfo(Info):
    def __init__(self):
        super(TvInfo, self).__init__()
        self.show = ''
        self.season = None
        self.episode = None
        self.network = ''
        self.seasons = None


class FetchersFactory(object):
    Fetchers = []
    FetcherInstances = []

    @classmethod
    def Register(cls, fetcher):
        cls.Fetchers.append(fetcher)

    @classmethod
    def InitFetchers(cls, language='en'):
        for fetcher in cls.Fetchers:
            cls.FetcherInstances.append(fetcher(language))

    @classmethod
    def GetFetcherBySource(cls, source: str, ftype: str):
        for fetcher in cls.FetcherInstances:
            if fetcher.source == source and ftype in fetcher.ftype:
                return fetcher
        raise Exception('No such Fetcher')

    # TODO : make it so it tries fetchers and returns one that works ?
    @classmethod
    def GetFetcherByType(cls, ftype: str):
        for fetcher in cls.FetcherInstances:
            if fetcher.ftype == ftype:
                return fetcher
        raise Exception('So such fetcher type {ftype}'.format(ftype=ftype))


class Fetcher(object):
    __metaclass__ = ABCMeta
    ftype = []
    source = ''

    @abstractmethod
    def fetch(self, showinfo):
        pass

    @abstractmethod
    def getArtwork(self, showinfo):
        pass


class Fetcher_tvdb(Fetcher):
    ftype = ['tv']
    source = 'tvdb'

    def __init__(self, language='en'):
        self.taglanguage = language
        self.fetcher = Tvdb(interactive=False, cache=True, banners=True, actors=True, forceConnect=True,
                            language=self.taglanguage)

        self.cache = None

    def fetch(self, showinfo):
        info = TvInfo()
        info.season = showinfo['season']
        info.episode = showinfo['episode']

        showdata = None

        for i in range(3):
            try:
                showdata = self.fetcher[showinfo['showid']]
                break
            except Exception as e:
                print(e)

        if showdata:
            seasondata = showdata[info.season]
            episodedata = seasondata[info.episode]
            info.seasons = len(seasondata)
            info.show = showdata['seriesname']
            genres = showdata['genre']

            if genres:
                info.genre = genres[0]

            info.network = showdata['network']
            info.contentrating = showdata['rating']

            info.title = episodedata['episodename']
            info.ldescription = episodedata['overview']
            info.description = info.ldescription
            info.date = episodedata['firstaired']

            info.director = episodedata['director']

            if episodedata['writer']:
                for name in episodedata['writer']:
                    if name != "":
                        info.writers.append(name)

            for actor in showdata["_actors"]:
                if actor['name'] != "" and len(info.cast) < 5:
                    info.cast.append(actor['name'])

            return info
        else:
            raise FetcherException

    def getArtwork(self, showinfo):

        showdata = None

        for i in range(3):
            try:
                showdata = self.fetcher[showinfo['showid']]
                break
            except Exception as e:
                print(e)

        poster = None
        bannerpath = ''

        if showdata:
            episodedata = showdata[showinfo['season']][showinfo['episode']]
            try:
                bannerlist = showdata['_banners']['season']['']
                for bannerid in bannerlist.keys():
                    if str(bannerlist[bannerid]['subKey']) == str(showinfo['season']):
                        bannerpath = bannerlist[bannerid]['_bannerpath']
                        break

                if bannerpath:
                    r = requests.get(bannerpath, stream=True)
                    if r.status_code == 200:
                        poster = os.path.join(tempfile.gettempdir(), 'poster-%s.jpg' % episodedata['episodename'])
                        with open(poster, 'wb') as f:
                            for chunk in r:
                                f.write(chunk)

            except Exception as e:
                poster = None  # Todo : Handle exceptions
                print(e)

        return poster


FetchersFactory.Register(Fetcher_tvdb)


class Fetcher_tmbd_movies(Fetcher):
    ftype = 'movies'
    source = 'tmdb'
    api_key = "45e408d2851e968e6e4d0353ce621c66"

    def __init__(self, language='en'):
        self.language = language
        self.fetcher = None

    def fetch(self, showinfo):

        info = MovieInfo()

        data = None

        try:
            tmdb.API_KEY = Fetcher_tmbd_movies.api_key
            movie = tmdb.Movies(showinfo['showid'])
            data = movie.info(language=self.language)

        except Exception:
            raise FetcherException

        if data:

            if hasattr(movie, 'titles'):
                for thetitle in movie.titles():
                    info.title = thetitle

            if not info.title:
                info.title = movie.title

            info.description = movie.tagline
            info.ldescription = movie.overview
            info.genre = movie.genres[0]['name']

            for thedate in movie.release_dates()['results']:
                if thedate['iso_3166_1'].lower() == self.language:
                    info.date = thedate['release_dates'][0]['release_date'][:10]
            if not info.date:
                info.date = movie.release_date

            for member in movie.credits()['cast']:
                info.cast.append(member['name'])
                if len(info.cast) == 5:
                    break

            for member in movie.credits()['crew']:
                if member['job'] == "Director" and len(info.director) < 5:
                    info.director.append(member['name'])

                if member['job'] == 'Producer' and len(info.producer) < 5:
                    info.producer.append(member['name'])

                if member['job'] == 'Author' and len(info.writers) < 5:
                    info.writers.append(member['name'])

            return info
        else:
            raise FetcherException

    def getArtwork(self, showinfo):
        """Fetches poster, write it to temp directory and returns path to poster file"""
        config = tmdb.Configuration().info()
        data = None
        poster = None

        try:
            tmdb.API_KEY = Fetcher_tmbd_movies.api_key
            movie = tmdb.Movies(showinfo['showid'])
            data = movie.info(language=self.language)
            images = movie.images(language=self.language)
        except:
            raise ArtworkException

        posters = posterCollection()

        for img in images['posters']:
            poster = Poster(rating=img['vote_average'], ratingcount=img['vote_count'], bannerpath=img['file_path'])
            posters.addPoster(poster)

        poster = posters.topPoster()
        poster.bannerpath = poster.bannerpath[1:] if poster.bannerpath.startswith('/') else poster.bannerpath

        imageurl = urljoin(config['images']['base_url'], 'w500' + '/' + poster.bannerpath)

        posterfile = os.path.join(tempfile.gettempdir(), poster.bannerpath)

        if data:
            r = requests.get(imageurl)
            if r.status_code == 200:
                with open(posterfile, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)

        return posterfile


FetchersFactory.Register(Fetcher_tmbd_movies)


class FetcherException(Exception):
    pass


class ArtworkException(FetcherException):
    pass


class Poster:
    # Simple container for all the poster parameters needed
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


if __name__ == '__main__':
    Fetchers = FetchersFactory()
    Fetchers.InitFetchers('en')

    # print(Fetchers.TVFetchers)

    showinfo = {
        'showid': 2501,
    }

    fetcher = Fetchers.GetFetcherBySource('tmdb', 'movies')
    test = fetcher.fetch(showinfo)

    print(test.title, test.description, test.writers)

    showinfo = {
        'showid': 176941,
        'season': 2,
        'episode': 2
    }
    fetcher = Fetchers.GetFetcherBySource('tvdb', 'tv')

    test = fetcher.fetch(showinfo)

    print(test.title, test.description, test.writers)

    poster = fetcher.getArtwork(showinfo)
