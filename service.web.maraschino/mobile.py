# -*- coding: utf-8 -*-
"""Ressources to use Maraschino on mobile devices"""

import jsonrpclib

from flask import render_template
from maraschino import app, logger

from maraschino.tools import *
from maraschino.noneditable import *

global sabnzbd_history_slots
sabnzbd_history_slots = None


@app.route('/mobile/')
@requires_auth
def mobile_index():
    xbmc = True
    available_modules = Module.query.order_by(Module.position)
    servers = XbmcServer.query.order_by(XbmcServer.position)

    if servers.count() == 0:
        xbmc = False

    return render_template('mobile/index.html',
        available_modules=available_modules,
        xbmc=xbmc,
        search=get_setting_value('search') == '1',
    )


from modules.recently_added import get_recently_added_episodes, get_recently_added_movies, \
                                   get_recently_added_albums, get_recent_xbmc_api_url


@app.route('/mobile/recent_episodes/')
@requires_auth
def recently_added_episodes():
    xbmc = jsonrpclib.Server(get_recent_xbmc_api_url('recently_added_server'))
    recently_added_episodes = get_recently_added_episodes(xbmc, mobile=True)

    return render_template('mobile/xbmc/recent_episodes.html',
        recently_added_episodes=recently_added_episodes[0],
        using_db=recently_added_episodes[1],
    )


@app.route('/mobile/recent_movies/')
@requires_auth
def recently_added_movies():
    xbmc = jsonrpclib.Server(get_recent_xbmc_api_url('recently_added_movies_server'))
    recently_added_movies = get_recently_added_movies(xbmc, mobile=True)

    return render_template('mobile/xbmc/recent_movies.html',
        recently_added_movies=recently_added_movies[0],
        using_db=recently_added_movies[1],
    )


@app.route('/mobile/recent_albums/')
@requires_auth
def recently_added_albums():
    xbmc = jsonrpclib.Server(get_recent_xbmc_api_url('recently_added_albums_server'))
    recently_added_albums = get_recently_added_albums(xbmc, mobile=True)

    return render_template('mobile/xbmc/recent_albums.html',
        recently_added_albums=recently_added_albums[0],
        using_db=recently_added_albums[1],
    )


@app.route('/mobile/xbmc/')
@requires_auth
def xbmc():
    servers = XbmcServer.query.order_by(XbmcServer.position)
    active_server = int(get_setting_value('active_server'))
    return render_template('mobile/xbmc/xbmc.html',
        servers=servers,
        active_server=active_server,
    )


@app.route('/mobile/movie_library/')
@requires_auth
def movie_library():
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        sort = {'method': 'label', 'ignorearticle': True}
        movies = xbmc.VideoLibrary.GetMovies(sort=sort, properties=['title', 'rating', 'year', 'thumbnail', 'tagline', 'playcount'])['movies']

    except:
        logger.log('Mobile :: XBMC :: Could not retrieve movie library', 'WARNING')

    return render_template('mobile/xbmc/movie_library.html',
        movies=movies,
    )


@app.route('/mobile/tv_library/')
@requires_auth
def tv_library():
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        sort = {'method': 'label', 'ignorearticle': True}
        TV = xbmc.VideoLibrary.GetTVShows(sort=sort, properties=['thumbnail'])['tvshows']

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve TV Shows: %s' % e, 'WARNING')

    return render_template('mobile/xbmc/tv_library.html',
        TV=TV,
    )


@app.route('/mobile/tvshow/<int:id>/')
@requires_auth
def tvshow(id):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        show = xbmc.VideoLibrary.GetSeasons(tvshowid=id, properties=['tvshowid', 'season', 'showtitle', 'playcount'], sort={'method': 'label'})['seasons']

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve TV Show [id: %i -  %s]' % (id, e), 'WARNING')

    return render_template('mobile/xbmc/tvshow.html',
        show=show,
    )


@app.route('/mobile/tvshow/<int:id>/<int:season>/')
@requires_auth
def season(id, season):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        episodes = xbmc.VideoLibrary.GetEpisodes(tvshowid=id, season=season, sort={'method': 'episode'}, properties=['tvshowid', 'season', 'showtitle', 'playcount'])['episodes']

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve TV Show [id: %i, season: %i -  %s]' % (id, season, e), 'WARNING')

    return render_template('mobile/xbmc/season.html',
        season=season,
        episodes=episodes,
    )


@app.route('/mobile/artist_library/')
@requires_auth
def artist_library():
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        sort = {'ignorearticle': True}
        artists = xbmc.AudioLibrary.GetArtists(sort=sort)['artists']

    except:
        logger.log('Mobile :: XBMC :: Could not retrieve artists from audio library', 'WARNING')
        artists = []

    return render_template('mobile/xbmc/artists.html',
        artists=artists,
    )


@app.route('/mobile/artist_library/<int:artistid>/')
@requires_auth
def album_library(artistid):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        version = xbmc.Application.GetProperties(properties=['version'])['version']['major']
        params = {'sort': {'ignorearticle': True}, 'properties': ['year']}

        if version < 12:  # Eden
            params['artistid'] = artistid
            params['properties'].extend(['artistid', 'artist'])
        else:  # Frodo
            params['filter'] = {'artistid': artistid}

        albums = xbmc.AudioLibrary.GetAlbums(**params)['albums']

        if version > 11:  # Frodo
            artist = xbmc.AudioLibrary.GetArtistDetails(artistid=artistid)['artistdetails']['label']
            for album in albums:
                album['artistid'] = artistid
                album['artist'] = artist
    except:
        logger.log('Mobile :: XBMC :: Could not retrieve albums from audio library', 'WARNING')
        albums = []

    return render_template('mobile/xbmc/albums.html',
        albums=albums,
    )


@app.route('/mobile/artist_library/<int:artistid>/<int:albumid>/')
@requires_auth
def song_library(artistid, albumid):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        version = xbmc.Application.GetProperties(properties=['version'])['version']['major']
        params = {'sort': {'ignorearticle': True}, 'properties': ['album', 'track', 'title']}

        if version < 12:  # Eden
            params['artistid'] = artistid
            params['albumid'] = albumid

        else:  # Frodo
            params['filter'] = {
                'albumid': albumid
            }

        songs = xbmc.AudioLibrary.GetSongs(**params)['songs']

    except:
        logger.log('Mobile :: XBMC :: Could not retrieve songs from audio library', 'WARNING')
        songs = []

    return render_template('mobile/xbmc/songs.html',
        songs=songs,
    )


@app.route('/mobile/movie/<int:id>/info/')
@requires_auth
def movie_info(id):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        properties = ['thumbnail', 'rating', 'director', 'genre', 'plot', 'year', 'trailer']
        movie = xbmc.VideoLibrary.GetMovieDetails(movieid=id, properties=properties)['moviedetails']

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve movie details [id: %i -  %s]' % (id, e), 'WARNING')

    return render_template('mobile/xbmc/movie-details.html',
        movie=movie
    )


@app.route('/mobile/tvshow/<int:id>/info/')
@requires_auth
def tvshow_info(id):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        properties = ['thumbnail', 'rating', 'studio', 'genre', 'plot']
        show = xbmc.VideoLibrary.GetTVShowDetails(tvshowid=id, properties=properties)['tvshowdetails']

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve TV Show details [id: %i -  %s]' % (id, e), 'WARNING')

    return render_template('mobile/xbmc/tvshow-details.html',
        show=show,
        banners=get_setting_value('library_use_bannerart') == '1'
    )


@app.route('/mobile/episode/<int:id>/info/')
@requires_auth
def episode_info(id):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        properties = ['thumbnail', 'firstaired', 'rating', 'plot', 'title']
        episode = xbmc.VideoLibrary.GetEpisodeDetails(episodeid=id, properties=properties)['episodedetails']

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve episode details [id: %i -  %s]' % (id, e), 'WARNING')

    return render_template('mobile/xbmc/episode-details.html',
        episode=episode
    )


@app.route('/mobile/artist/<int:id>/info/')
@requires_auth
def artist_info(id):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        properties = ['description', 'thumbnail', 'genre']
        artist = xbmc.AudioLibrary.GetArtistDetails(artistid=id, properties=properties)['artistdetails']

        for k in artist:
            if isinstance(artist[k], list):
                artist[k] = " / ".join(artist[k])

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve artist details [id: %i -  %s]' % (id, e), 'WARNING')

    return render_template('mobile/xbmc/artist-details.html',
        artist=artist
    )


@app.route('/mobile/album/<int:id>/info/')
@requires_auth
def album_info(id):
    try:
        xbmc = jsonrpclib.Server(server_api_address())
        properties = ['title', 'artist', 'year', 'genre', 'description', 'rating', 'thumbnail']
        album = xbmc.AudioLibrary.GetAlbumDetails(albumid=id, properties=properties)['albumdetails']

        for k in album:
            if isinstance(album[k], list):
                album[k] = " / ".join(album[k])

    except Exception as e:
        logger.log('Mobile :: XBMC :: Could not retrieve album details [id: %i -  %s]' % (id, e), 'WARNING')

    return render_template('mobile/xbmc/album-details.html',
        album=album
    )

from modules.sickbeard import sickbeard_api, get_pic


@app.route('/mobile/sickbeard/')
@requires_auth
def sickbeard():

    try:
        sickbeard = sickbeard_api('/?cmd=future&sort=date')

        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']
            for time in sickbeard:
                for episode in sickbeard[time]:
                    episode['image'] = get_pic(episode['tvdbid'], 'banner')

    except Exception as e:
        logger.log('Could not retrieve sickbeard - %s]' % (e), 'WARNING')
        sickbeard = None

    return render_template('mobile/sickbeard/coming_episodes.html',
        coming_episodes=sickbeard,
    )


@app.route('/mobile/sickbeard/all/')
@requires_auth
def sickbeard_all():

    try:
        sickbeard = sickbeard_api('/?cmd=shows&sort=name')

        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']

            for show in sickbeard:
                sickbeard[show]['url'] = get_pic(sickbeard[show]['tvdbid'], 'banner')

    except Exception as e:
        logger.log('Could not retrieve sickbeard - %s]' % (e), 'WARNING')
        sickbeard = None

    return render_template('mobile/sickbeard/all.html',
        shows=sickbeard,
    )


@app.route('/mobile/sickbeard/history/')
@requires_auth
def sickbeard_history():

    try:
        sickbeard = sickbeard_api('/?cmd=history&limit=30')

        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']

    except Exception as e:
        logger.log('Could not retrieve sickbeard - %s]' % (e), 'WARNING')
        sickbeard = None

    return render_template('mobile/sickbeard/history.html',
        history=sickbeard,
    )


@app.route('/mobile/sickbeard/show/<int:id>/')
@requires_auth
def sickbeard_show(id):
    params = '/?cmd=show&tvdbid=%s' % id

    try:
        sickbeard = sickbeard_api(params)

        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']
            sickbeard['tvdbid'] = id

    except Exception as e:
        logger.log('Could not retrieve sickbeard - %s]' % (e), 'WARNING')
        sickbeard = None

    return render_template('mobile/sickbeard/show.html',
        show=sickbeard,
    )


@app.route('/mobile/sickbeard/show/<int:id>/<int:season>/')
@requires_auth
def sickbeard_season(id, season):
    params = '/?cmd=show.seasons&tvdbid=%s&season=%s' % (id, season)

    try:
        sickbeard = sickbeard_api(params)

        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']
            numbers = sorted(sickbeard, key=int)

    except Exception as e:
        logger.log('Could not retrieve sickbeard - %s]' % (e), 'WARNING')
        sickbeard = None

    return render_template('mobile/sickbeard/season.html',
        season_number=season,
        season=sickbeard,
        id=id,
        numbers=numbers,
    )


@app.route('/mobile/sickbeard/show/<int:id>/<int:season>/<int:episode>/')
@requires_auth
def sickbeard_episode(id, season, episode):
    params = '/?cmd=episode&tvdbid=%s&season=%s&episode=%s&full_path=1' % (id, season, episode)

    try:
        sickbeard = sickbeard_api(params)

        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']

    except Exception as e:
        logger.log('Could not retrieve sickbeard - %s]' % (e), 'WARNING')
        sickbeard = None

    return render_template('mobile/sickbeard/episode.html',
        season_number=season,
        episode_number=episode,
        episode=sickbeard,
        id=id,
    )


@app.route('/mobile/sickbeard/episode_options/<int:id>/<int:season>/<int:episode>/')
@requires_auth
def sickbeard_episode_options(id, season, episode):

    return render_template('mobile/sickbeard/episode_options.html',
        season_number=season,
        episode_number=episode,
        show_number=id,
    )


@app.route('/mobile/sickbeard/search/')
@app.route('/mobile/sickbeard/search/<query>/')
def sickbeard_search(query=None):
    from urllib2 import quote
    sickbeard = None
    if query:
        try:
            sickbeard = sickbeard_api('/?cmd=sb.searchtvdb&name=%s' % (quote(query)))
            sickbeard = sickbeard['data']['results']

        except Exception as e:
            logger.log('Mobile :: SickBeard :: Could not retrieve shows - %s]' % (e), 'WARNING')

    return render_template('mobile/sickbeard/search.html',
        results=sickbeard,
        query=query,
    )


from modules.couchpotato import couchpotato_api


@app.route('/mobile/couchpotato/')
@requires_auth
def couchpotato():
    try:
        couchpotato = couchpotato_api('movie.list', params='status=active')
        if couchpotato['success'] and not couchpotato['empty']:
            couchpotato = couchpotato['movies']

    except Exception as e:
        logger.log('Mobile :: CouchPotato :: Could not retrieve Couchpotato - %s]' % (e), 'WARNING')
        couchpotato = None

    return render_template('mobile/couchpotato/wanted.html',
        wanted=couchpotato,
    )


@app.route('/mobile/couchpotato/all/')
@requires_auth
def couchpotato_all():
    try:
        couchpotato = couchpotato_api('movie.list', params='status=done')
        if couchpotato['success'] and not couchpotato['empty']:
            couchpotato = couchpotato['movies']

    except Exception as e:
        logger.log('Mobile :: CouchPotato :: Could not retrieve Couchpotato - %s]' % (e), 'WARNING')
        couchpotato = None

    return render_template('mobile/couchpotato/all.html',
        all=couchpotato,
    )


@app.route('/mobile/couchpotato/history/')
@requires_auth
def couchpotato_history():
    unread = 0
    try:
        couchpotato = couchpotato_api('notification.list')
        if couchpotato['success'] and not couchpotato['empty']:
            couchpotato = couchpotato['notifications']
            for notification in couchpotato:
                if not notification['read']:
                    unread = unread + 1

    except Exception as e:
        logger.log('Mobile :: CouchPotato :: Could not retrieve Couchpotato - %s]' % (e), 'WARNING')
        couchpotato = None

    return render_template('mobile/couchpotato/history.html',
        history=couchpotato,
        unread=unread,
    )


@app.route('/mobile/couchpotato/movie/<id>/')
def couchpotato_movie(id):
    try:
        couchpotato = couchpotato_api('media.get', 'id=%s' % id)
        if couchpotato['success']:
            couchpotato = couchpotato['media']

    except Exception as e:
        logger.log('Mobile :: CouchPotato :: Could not retrieve movie - %s]' % (e), 'WARNING')

    return render_template('mobile/couchpotato/movie.html',
        movie=couchpotato,
    )


@app.route('/mobile/couchpotato/search/')
@app.route('/mobile/couchpotato/search/<query>/')
def couchpotato_search(query=None):
    couchpotato = None
    if query:
        try:
            couchpotato = couchpotato_api('movie.search', params='q=%s' % query)
            if couchpotato['success']:
                couchpotato = couchpotato['movie']

        except Exception as e:
            logger.log('Mobile :: CouchPotato :: Could not retrieve movie - %s]' % (e), 'WARNING')

    return render_template('mobile/couchpotato/search.html',
        results=couchpotato,
        query=query,
    )

from modules.headphones import *


@app.route('/mobile/headphones/')
@requires_auth
def headphones_wanted():
    albums = xhr_headphones_upcoming(mobile=True)
    upcoming = albums[0]
    wanted = albums[1]

    if upcoming == 'empty':
        upcoming = []

    if wanted == 'empty':
        wanted = []

    return render_template('mobile/headphones/wanted.html',
        upcoming=upcoming,
        wanted=wanted
    )


@app.route('/mobile/headphones/history/')
@requires_auth
def headphones_history():
    history = xhr_headphones_history(mobile=True)

    return render_template('mobile/headphones/history.html',
        history=history
    )


@app.route('/mobile/headphones/all/')
@requires_auth
def headphones_all():
    artists = xhr_headphones_artists(mobile=True)

    return render_template('mobile/headphones/all.html',
        artists=artists
    )


@app.route('/mobile/headphones/album/<albumid>/')
@requires_auth
def headphones_album(albumid):
    album = xhr_headphones_album(albumid, mobile=True)

    return render_template('mobile/headphones/album.html',
        album=album
    )


@app.route('/mobile/headphones/artist/<artistid>/')
@requires_auth
def headphones_artist(artistid):
    artist = xhr_headphones_artist(artistid, mobile=True)

    return render_template('mobile/headphones/artist.html',
        artist=artist
    )


@app.route('/mobile/headphones/search/<type>/')
@app.route('/mobile/headphones/search/<type>/<query>/')
def headphones_search(type, query=None):
    results = None
    if query:
        results = xhr_headphones_search(type, query, mobile=True)

    return render_template('mobile/headphones/search.html',
        type=type,
        results=results,
        query=query
    )


@app.route('/mobile/headphones/artist/action/<artistid>/<action>/')
def headphones_artist_action(artistid, action):
    result = xhr_headphones_artist_action(artistid, action, mobile=True)
    return result


@app.route('/mobile/headphones/album/<albumid>/<status>/')
def headphones_album_status(albumid, status):
    result = xhr_headphones_album_status(albumid, status, mobile=True)
    return result


from modules.sabnzbd import sabnzbd_api


@app.route('/mobile/sabnzbd/')
@requires_auth
def sabnzbd():
    try:
        sabnzbd = sabnzbd_api(method='queue')
        sabnzbd = sabnzbd['queue']
        download_speed = format_number(int((sabnzbd['kbpersec'])[:-3]) * 1024) + '/s'
        if sabnzbd['speedlimit']:
            sabnzbd['speedlimit'] = format_number(int((sabnzbd['speedlimit'])) * 1024) + '/s'

    except Exception as e:
        logger.log('Mobile :: SabNZBd+ :: Could not retrieve SabNZBd - %s]' % (e), 'WARNING')
        sabnzbd = None

    return render_template('mobile/sabnzbd/sabnzbd.html',
        queue=sabnzbd,
        download_speed=download_speed,
    )


@app.route('/mobile/sabnzbd/history/')
@requires_auth
def sabnzbd_history():
    global sabnzbd_history_slots
    try:
        sabnzbd = sabnzbd_api(method='history', params='&limit=50')
        sabnzbd = sabnzbd_history_slots = sabnzbd['history']

    except Exception as e:
        logger.log('Mobile :: SabNZBd+ :: Could not retrieve SabNZBd - %s]' % (e), 'WARNING')
        sabnzbd = None

    return render_template('mobile/sabnzbd/history.html',
        history=sabnzbd,
    )


@app.route('/mobile/sabnzbd/queue/<id>/')
@requires_auth
def sabnzbd_queue_item(id):
    try:
        sab = sabnzbd_api(method='queue')
        sab = sab['queue']

        for item in sab['slots']:
            if item['nzo_id'] == id:
                return render_template('mobile/sabnzbd/queue_item.html',
                    item=item,
                )
    except Exception as e:
        logger.log('Mobile :: SabNZBd+ :: Could not retrieve SabNZBd - %s]' % (e), 'WARNING')

    return sabnzbd()


@app.route('/mobile/sabnzbd/history/<id>/')
@requires_auth
def sabnzbd_history_item(id):
    global sabnzbd_history_slots
    if sabnzbd_history_slots:
        for item in sabnzbd_history_slots['slots']:
            if item['nzo_id'] == id:
                return render_template('mobile/sabnzbd/history_item.html',
                    item=item,
                )

        return sabnzbd_history()
    else:
        try:
            sabnzbd = sabnzbd_api(method='history', params='&limit=50')
            sabnzbd = sabnzbd_history_slots = sabnzbd['history']

            for item in sabnzbd_history_slots['slots']:
                if item['nzo_id'] == id:
                    return render_template('mobile/sabnzbd/history_item.html',
                        item=item,
                    )
        except Exception as e:
            logger.log('Mobile :: SabNZBd+ :: Could not retrieve SabNZBd - %s]' % (e), 'WARNING')
            sabnzbd = None

        return render_template('mobile/sabnzbd/history.html',
            history=sabnzbd,
        )


from modules.search import cat_newznab, newznab, get_newznab_sites
from maraschino.models import NewznabSite


@app.route('/mobile/search/')
@app.route('/mobile/search/<site>/')
def search(site=1):
    site = int(site)
    newznab = NewznabSite.query.filter(NewznabSite.id == site).first()
    categories = cat_newznab(newznab.url)

    return render_template('mobile/search.html',
        query=None,
        site=site,
        categories=categories,
        newznab_sites=get_newznab_sites(),
        category=0
    )


@app.route('/mobile/search/<site>/<category>/<maxage>/')
@app.route('/mobile/search/<site>/<category>/<maxage>/<term>/')
@requires_auth
def mobile_search_results(site, category='0', maxage='0', term=''):
    if site:
        site = int(site)
        url = NewznabSite.query.filter(NewznabSite.id == site).first().url
        categories = cat_newznab(url)
        results = newznab(site=site, category=category, maxage=maxage, term=term, mobile=True)

    return render_template('mobile/search.html',
        query=term,
        site=site,
        categories=categories,
        newznab_sites=get_newznab_sites(),
        category=category,
        results=results
    )


from modules.traktplus import *


@app.route('/mobile/trakt/')
@requires_auth
def mobile_trakt():
    return render_template('mobile/trakt/trakt.html')


@app.route('/mobile/trakt/trending/')
@app.route('/mobile/trakt/trending/<media>/')
@requires_auth
def mobile_trakt_trending(media=None):
    if not media:
        media = get_setting_value('trakt_default_media')

    trending = xhr_trakt_trending(type=media, mobile=True)

    return render_template('mobile/trakt/trending.html',
        trending=trending,
        media=media
    )


@app.route('/mobile/trakt/summary/<media>/<id>/')
@app.route('/mobile/trakt/summary/<media>/<id>/<season>/<episode>/')
@requires_auth
def mobile_trakt_summary(media, id, season=None, episode=None):

    summary = xhr_trakt_summary(type=media, id=id, season=season, episode=episode, mobile=True)

    if 'genres' in summary:
        summary['genres'] = " / ".join(summary['genres'])

    if media == 'show':
        url = 'http://api.trakt.tv/show/shouts.json/%s/%s' % (trakt_apikey(), id)
    elif media == 'episode':
        url = 'http://api.trakt.tv/show/episode/shouts.json/%s/%s/%s/%s' % (trakt_apikey(), id, season, episode)
    else:
        url = 'http://api.trakt.tv/movie/shouts.json/%s/%s' % (trakt_apikey(), id)

    try:
        shouts = trak_api(url)
    except:
        logger.log('TRAKT :: Failed to retrieve shouts for %s: %s' % (media, id), 'ERROR')
        shouts = []

    return render_template('mobile/trakt/summary.html',
        summary=summary,
        shouts=shouts,
        media=media
    )


@app.route('/mobile/trakt/recommendations/')
@app.route('/mobile/trakt/recommendations/<media>/')
@requires_auth
def mobile_trakt_recommendations(media=None):
    if not media:
        media = get_setting_value('trakt_default_media')

    recommendations = xhr_trakt_recommendations(type=media, mobile=True)

    return render_template('mobile/trakt/recommendations.html',
        recommendations=recommendations,
        media=media
    )


@app.route('/mobile/trakt/activity/')
@app.route('/mobile/trakt/activity/<type>/')
@requires_auth
def mobile_trakt_activity(type='friends'):
    activity = xhr_trakt_activity(type=type, mobile=True)

    return render_template('mobile/trakt/activity.html',
        activity=activity,
        type=type
    )


@app.route('/mobile/trakt/profile/')
@app.route('/mobile/trakt/profile/<user>/')
@requires_auth
def mobile_trakt_profile(user=None):
    profile = xhr_trakt_profile(user=user, mobile=True)

    return render_template('mobile/trakt/profile.html',
        profile=profile,
    )


@app.route('/mobile/trakt/calendar/<type>/')
@requires_auth
def mobile_trakt_calendar(type):
    calendar = xhr_trakt_calendar(type=type, mobile=True)

    return render_template('mobile/trakt/calendar.html',
        calendar=calendar,
        type=type
    )


@app.route('/mobile/trakt/friends/')
@app.route('/mobile/trakt/friends/<user>/')
@requires_auth
def mobile_trakt_friends(user=None):
    friends = xhr_trakt_friends(user=user, mobile=True)

    return render_template('mobile/trakt/friends.html',
        friends=friends,
        user=user
    )


@app.route('/mobile/trakt/library/<user>/')
@app.route('/mobile/trakt/library/<user>/<media>/')
@requires_auth
def mobile_trakt_library(user, media=None):
    if not media:
        media = get_setting_value('trakt_default_media')

    library = xhr_trakt_library(user=user, type=media, mobile=True)

    return render_template('mobile/trakt/user_media.html',
        trakt=library,
        user=user,
        media=media,
        view='library',
    )


@app.route('/mobile/trakt/watchlist/<user>/')
@app.route('/mobile/trakt/watchlist/<user>/<media>/')
@requires_auth
def mobile_trakt_watchlist(user, media=None):
    if not media:
        media = get_setting_value('trakt_default_media')

    watchlist = xhr_trakt_watchlist(user=user, type=media, mobile=True)

    return render_template('mobile/trakt/user_media.html',
        trakt=watchlist,
        user=user,
        media=media,
        view='watchlist',
    )


@app.route('/mobile/trakt/rated/<user>/<media>/')
@app.route('/mobile/trakt/rated/<user>/')
@requires_auth
def mobile_trakt_rated(user, media=None):
    if not media:
        media = get_setting_value('trakt_default_media')

    watchlist = xhr_trakt_rated(user=user, type=media, mobile=True)

    return render_template('mobile/trakt/user_media.html',
        trakt=watchlist,
        user=user,
        media=media,
        view='rated',
    )


@app.route('/mobile/trakt/get_lists/<user>/')
@requires_auth
def mobile_trakt_lists(user):
    lists = xhr_trakt_get_lists(user=user, mobile=True)

    return render_template('mobile/trakt/lists.html',
        lists=lists,
        user=user,
        title='Lists'
    )


@app.route('/mobile/trakt/list/<slug>/<user>/')
@requires_auth
def mobile_trakt_custom_list(slug, user):
    custom_list = xhr_trakt_custom_list(slug=slug, user=user, mobile=True)

    return render_template('mobile/trakt/lists.html',
        custom_list=custom_list,
        user=user,
        title=custom_list['name']
    )


@app.route('/xhr/trakt/progress/<user>/')
@app.route('/xhr/trakt/progress/<user>/<type>/')
@requires_auth
def mobile_trakt_progress(user, type=None):
    if not type:
        type = 'watched'

    progress = xhr_trakt_progress(user=user, type=type, mobile=True)

    return render_template('mobile/trakt/progress.html',
        progress=progress,
        user=user,
        type=type
    )


from maraschino.database import db_session
from maraschino.models import Script
import os, platform, ctypes, subprocess, datetime

@app.route('/mobile/script_launcher/')
@requires_auth
def script_launcher():
    scripts = []
    scripts_db = Script.query.order_by(Script.id)

    if scripts_db.count() > 0:
        for script_db in scripts_db:
            script = {}
            script['script'] = script_db.script
            script['label'] = script_db.label
            script['status'] = script_db.status
            script['id'] = script_db.id
            scripts.append(script)

    return render_template('mobile/script_launcher/script_launcher.html',
        scripts = scripts,
    )

@app.route('/mobile/script_launcher/script_status/<script_id>', methods=['GET', 'POST'])
def script_status(script_id):

    status = request.form['status']

    if status == '':
        return jsonify({ 'status': 'error: there was no status passed in' })

    script = Script.query.filter(Script.id == script_id).first()
    script.status = status

    try:
        db_session.add(script)
        db_session.commit()

    except:
        return jsonify({ 'status': 'error' })

    return script_launcher()

@app.route('/mobile/script_launcher/start_script/<int:script_id>')
@requires_auth
def start_script(script_id):
    #first get the script we want
    script = None
    message = None
    script = Script.query.filter(Script.id == script_id).first()
    now = datetime.datetime.now()

    command = os.path.join(maraschino.SCRIPT_DIR,script.script)

    if (script.parameters):
        command = ''.join([command, ' ', script.parameters])

    #Parameters needed for scripts that update
    host = maraschino.HOST
    port = maraschino.PORT
    webroot = maraschino.WEBROOT

    if not webroot:
        webroot = '/'

    file_ext = os.path.splitext(script.script)[1]

    if (file_ext == '.py'):
        if (script.updates == 1):        
            #these are extra parameters to be passed to any scripts ran, so they 
            #can update the status if necessary
            extras = '--i "%s" --p "%s" --s "%s" --w "%s"' % (host, port, script.id, webroot)

            #the command in all its glory
            command = ''.join([command, ' ', extras])
            script.status="Script Started at: %s" % now.strftime("%m-%d-%Y %H:%M")
        else:
            script.status="Last Ran: %s" % now.strftime("%m-%d-%Y %H:%M")

        command =  ''.join(['python ', command])

    elif (file_ext in ['.sh', '.pl', '.cmd']):
        if (script.updates == 1):
            extras = '%s %s %s %s' % (host, port, script.id, webroot)
            #the command in all its glory
            command = ''.join([command, ' ', extras])
            script.status="Script Started at: %s" % now.strftime("%m-%d-%Y %H:%M")
        else:
            script.status="Last Ran: %s" % now.strftime("%m-%d-%Y %H:%M")

        if(file_ext == '.pl'):
            command = ''.join(['perl ', command])

        if(file_ext == '.cmd'):
            command = ''.join([command])


    logger.log('SCRIPT_LAUNCHER :: %s' % command, 'INFO')
    #now run the command
    subprocess.Popen(command, shell=True)

    db_session.add(script)
    db_session.commit()

    return script_launcher()  
