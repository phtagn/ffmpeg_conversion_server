import os
import tempfile
from abc import abstractmethod, ABCMeta

import requests
import tmdbsimple as tmdb
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
        self.posterurl = ''

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
    _Fetchers = []
    FetcherInstances = []

    @classmethod
    def Register(cls, fetcher):
        cls._Fetchers.append(fetcher)

    @classmethod
    def GetBySource(cls, source: str, language='en'):
        for fetcher in cls._Fetchers:
            if fetcher.source == source:
                return fetcher(language)
        raise Exception('No such Fetcher')

    # TODO : make it so it tries fetchers and returns one that works ?
    @classmethod
    def GetByType(cls, ftype: str, language='en'):
        for fetcher in cls._Fetchers:
            if fetcher.ftype == ftype:
                return fetcher(language)
        raise Exception('So such fetcher type {ftype}'.format(ftype=ftype))

    @classmethod
    def GetFromJob(cls, job, language='en'):
        if job.id_type == 'tvdb':
            return cls.GetBySource('tvdb', language)
        if job.id_type == 'tmdb':
            return cls.GetBySource('tmdb', language)
        if job.id_type == 'imdb':
            return cls.GetBySource('tmdb', language)

class Fetcher(object):
    __metaclass__ = ABCMeta
    ftype = []
    source = ''

    @abstractmethod
    def fetch(self, job):
        pass

    def getArtwork(self):
        pass


class Fetcher_tvdb(Fetcher):
    ftype = ['tv']
    source = 'tvdb'

    def __init__(self, language='en'):
        fetcher = Tvdb()
        if language in fetcher.config['valid_languages']:
            self.language = language
        else:
            self.language = 'en'

        self.fetcher = Tvdb(interactive=False, cache=True, banners=True, actors=True, forceConnect=True,
                            language=self.language)

        self.cache = None

    def fetch(self, job):
        info = TvInfo()
        info.season = job.season
        info.episode = job.episode

        showdata = None

        for i in range(3):
            try:
                showdata = self.fetcher[job.id]
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

            bannerlist = showdata['_banners']['season']['']
            for bannerid in bannerlist.keys():
                if str(bannerlist[bannerid]['subKey']) == str(info.season):
                    info.posterurl = bannerlist[bannerid]['_bannerpath']
                    break

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


class FetcherTmdb(Fetcher):
    ftype = ['movies', 'tv']
    source = 'tmdb'
    api_key = '45e408d2851e968e6e4d0353ce621c66'

    def __init__(self, language='en'):
        tmdb.API_KEY = FetcherTmdb.api_key
        self.config = tmdb.Configuration().info()
        self.language = language

        self.definition = 'original'

    def fetch(self, job):
        search = tmdb.Find(job.id)

        if job.id_type == 'tmdb':
            return self._fetchMovie(job.id)

        elif job.id_type == 'tvdb':
            info = search.info(external_source='tvdb_id')
            if len(info['tv_results']) == 1:
                return self._fetchTV(info['tv_results'][0]['id'], job.season, job.episode)

        elif job.id_type == 'imdb':
            info = search.info(external_source='imdb_id')
            if len(info['movie_results']) == 1:
                return self._fetchMovie(info['movie_results'][0]['id'])

    def _fetchTV(self, tmdbid, season, episode):
        # seasondata = None
        episodedata = None
        showdata = None
        try:
            fetcher = tmdb.TV_Seasons(tmdbid, season)
            showdata = tmdb.TV(tmdbid).info(language=self.language)
            seasondata = tmdb.TV_Seasons(tmdbid, season).info(language=self.language)
            episodedata = tmdb.TV_Episodes(tmdbid, season, episode).info(language=self.language)
        except:
            pass

        if showdata:
            info = TvInfo()
            # Show info
            info.seasons = showdata['number_of_seasons']
            info.show = showdata['name']
            for net in showdata['networks']:
                if net['origin_country'] == showdata['origin_country'][0]:
                    info.network = net['name']
                    break
            info.genre = showdata['genres'][0]['name']

            # Season info
            info.posterurl = self._getposterpath(fetcher)

            info.episode = episode
            info.season = season
            info.title = episodedata['name']
            info.date = episodedata['air_date']
            info.ldescription = episodedata['overview']
            for member in episodedata['crew']:
                if member['job'] == 'Director':
                    info.director.append(member['name'])
                if member['job'] == 'Writer':
                    info.writers.append(member['name'])

            return info

    def _fetchMovie(self, tmdbid):
        info = MovieInfo()
        try:
            movie = tmdb.Movies(tmdbid)
            moviedata = movie.info(language=self.language)

        except Exception:
            raise FetcherException

        if moviedata:

            info.title = moviedata['title']
            info.description = moviedata['tagline']
            info.ldescription = moviedata['overview']
            info.genre = movie.genres[0]['name']
            info.posterurl = self._getposterpath(movie)

            for thedate in movie.release_dates()['results']:
                if thedate['iso_3166_1'].lower() == self.language:
                    info.date = thedate['release_dates'][0]['release_date'][:10]

            if not info.date:
                info.date = moviedata['release_date']

            for member in movie.credits()['cast']:
                info.cast.append(member['name'])
                if len(info.cast) == 5:
                    break

            for member in movie.credits()['crew']:
                if member['job'] == "Director" and len(info.director) < 5:
                    info.director.append(member['name'])
                    continue
                if member['job'] == 'Producer' and len(info.producer) < 5:
                    info.producer.append(member['name'])
                    continue
                if member['job'] == 'Writer' or member['job'] == 'Author' and len(info.writers) < 5:
                    info.writers.append(member['name'])
                    continue
            return info
        else:
            raise FetcherException

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
        return '{base_url}{definition}{path}'.format(base_url=self.config['images']['base_url'],
                                                     definition=self.definition,
                                                     path=poster.bannerpath)


FetchersFactory.Register(FetcherTmdb)


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
    import jobs

    tv = {'jobtype': 'tvshow',
          'inputfile': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
          'original': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
          'season': 2,
          'episode': 2,
          'id': 176941,
          'id_type': 'tvdb',
          'requester': 'sickrage',
          'settings': '/Users/Jon/Downloads/config/testsettings.ini'
          }

    movie = {
        'jobtype': 'movie',
        'inputfile': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'original': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'id': 2501,
        'id_type': 'tmdb',
        'requester': 'sickrage',
        'settings': '/Users/Jon/Downloads/config/testsettings.ini'
    }

    movieimdb = {
        'jobtype': 'movie',
        'inputfile': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'original': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'id': 'tt5699154',
        'id_type': 'imdb',
        'requester': 'sickrage',
        'settings': '/Users/Jon/Downloads/config/testsettings.ini'
    }

    tvjob = jobs.TVJob(tv)
    moviejob = jobs.MovieJob(movie)
    imdbjob = jobs.MovieJob(movieimdb)
    factory = FetchersFactory()

    fetcher1 = factory.GetFromJob(tvjob, 'fr')
    fetcher2 = factory.GetFromJob(moviejob, 'fr')
    fetcher3 = factory.GetFromJob(imdbjob, 'fr')

    toto = fetcher1.fetch(tvjob)
    print(toto.title, toto.ldescription, toto.writers, toto.posterurl, sep="\n")
