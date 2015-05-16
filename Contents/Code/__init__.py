
NAME                    = "Subsonic"
PREFIX                  = "/music/subsonic"
CACHE_INTERVAL          = 604800
ART                     = "art-default.png"
ICON                    = "icon-default.png"
NOART                   = "noart-default.png"
FOLDER                  = "folder.png"
ARTIST                  = "{http://subsonic.org/restapi}artist"
ALBUM                   = "{http://subsonic.org/restapi}album"
SONG                    = "{http://subsonic.org/restapi}song"
DIRECTORY               = "{http://subsonic.org/restapi}directory"
CHILD                   = "{http://subsonic.org/restapi}child"
SUBSONIC_API_VERSION    = "1.9.0"
SUBSONIC_CLIENT         = "plex"
NS                      = {'media': 'http://subsonic.org/restapi'}
CACHE_1WEEK             = 604800

import binascii

####################################################################################################

def L(string):
  local_string = Locale.LocalString(string)
  return str(local_string).decode()

def Start():
  #HTTP.CacheTime = CACHE_1WEEK
  Locale.DefaultLocale = Prefs["language"].split("/")[1]

@handler(PREFIX, NAME)
def main():
  dir = ObjectContainer(title1="Subsonic")
  dir.add(DirectoryObject(title=L("menu_folders"), key = PREFIX + '/getFolders', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_styles"), key = PREFIX + '/getGenres', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_random"), key = PREFIX + '/getAlbumList/random/menu_random', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_newest"), key = PREFIX + '/getAlbumList/newest/menu_newest', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_highest"), key = PREFIX + '/getAlbumList/highest/menu_highest', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_frequent"), key = PREFIX + '/getAlbumList/frequent/menu_frequent', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_recent"), key = PREFIX + '/getAlbumList/recent/menu_recent', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_playlists"), key = PREFIX + '/getPlaylists', thumb=R(FOLDER)))
  dir.add(DirectoryObject(title=L("menu_artists"), key = PREFIX + '/getArtists', thumb=R(FOLDER)))

  #add preferences option
  dir.add(PrefsObject(title="Preferences"))
  return dir

@route(PREFIX + '/getPlaylists')
def getPlaylists():
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L("oc_title_playlists"))
  element = XML.ElementFromURL(makeURL("getPlaylists.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, "{http://subsonic.org/restapi}playlist"):
    title       = item.get("name")
    artist      = item.get("owner")
    id          = item.get("id")
    coverArt    = item.get("coverArt")
    key         = PREFIX + '/getPlaylist/' + id
    if coverArt:
      thumbURL = makeURL("getCoverArt.view", id=coverArt)
      dir.add(DirectoryObject(title=title, key=key, thumb=thumbURL))
    else:
      dir.add(DirectoryObject(title=title, key=key, thumb=R(NOART)))
    #return dir
  return dir

@route(PREFIX + '/getPlaylist/{playlistID}')
def getPlaylist(playlistID):
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  element = XML.ElementFromURL(makeURL("getPlaylist.view", id=playlistID), cacheTime=CACHE_INTERVAL)
  pl_title = "Playlist: " + element.xpath('./media:playlist/@name', namespaces=NS)[0]
  dir = ObjectContainer(title1=pl_title)
  for item in searchElementTree(element, "{http://subsonic.org/restapi}entry"):
    title       = item.get("title")
    artist      = item.get("artist")
    album       = item.get("album")
    id          = item.get("id")
    coverArt    = item.get("coverArt")
    if coverArt:
      thumbURL = makeURL("getCoverArt.view", id=coverArt)
    else:
      thumbURL = R(NOART)
    rating_key  = id
    duration = 1000 * int(item.get("duration"))
    url = makeURL("stream.view", id=id, format=container)
    dir.add(TrackObject(
      artist=artist, 
      album=album, 
      title=title, 
      duration=duration, 
      key=id, #might need to change this line eventually to return metadata instead of playing track
      rating_key=rating_key,
      thumb=thumbURL,
      items = [
        MediaObject(
          parts = [
            PartObject(key=Callback(playAudio, url=url, ext=container))
          ],
          container = container,
          audio_codec = audio_codec,
          audio_channels = 2,
          platforms=[]
        )
      ]))
  return dir

@route(PREFIX + '/getAlbumList/{listType}/{title}')
def getAlbumList(listType, title):
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L(title))
  element = XML.ElementFromURL(makeURL("getAlbumList.view", type=listType, size="50"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, "{http://subsonic.org/restapi}album"):
    title       = item.get("title")
    artist      = item.get("artist")
    id          = item.get("id")
    coverArt    = item.get("coverArt")
    key         = PREFIX + '/getAlbum/' + id
    if coverArt:
      thumbURL = makeURL("getCoverArt.view", id=coverArt)
      dir.add(DirectoryObject(title=title, key=key, thumb=thumbURL))
    else:
      dir.add(DirectoryObject(title=title, key=key, thumb=R(NOART)))
    #return dir
  return dir


@route(PREFIX + '/getGenres')
def getGenres():
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L("oc_title_styles"))
  element = XML.ElementFromURL(makeURL("getGenres.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, "{http://subsonic.org/restapi}genre"):
    title       = item.text
    key         = PREFIX + '/getSongsByGenre/' + String.Encode(title)
    dir.add(DirectoryObject(title=title, key=key))
    #return dir
  return dir

@route(PREFIX + '/getSongsByGenre/{genre}')
def getSongsByGenre(genre):
  genre = String.Decode(genre)
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L("oc_title_styles"))
  element = XML.ElementFromURL(makeURL("getSongsByGenre.view", genre=String.Quote(genre), count="50"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, "{http://subsonic.org/restapi}song"):
    title       = item.get("title")
    artist      = item.get("artist")
    album       = item.get("album")
    id          = item.get("id")
    coverArt    = item.get("coverArt")
    if coverArt:
      thumbURL = makeURL("getCoverArt.view", id=coverArt)
    else:
      thumbURL = R(NOART)
    rating_key  = id
    duration = 1000 * int(item.get("duration"))
    url = makeURL("stream.view", id=id, format=container)
    dir.add(TrackObject(
      artist=artist, 
      album=album, 
      title=title, 
      duration=duration, 
      key=id, #might need to change this line eventually to return metadata instead of playing track
      rating_key=rating_key,
      thumb=thumbURL,
      items = [
        MediaObject(
          parts = [
            PartObject(key=Callback(playAudio, url=url, ext=container))
          ],
          container = container,
          audio_codec = audio_codec,
          audio_channels = 2,
          platforms=[]
        )
      ]))
  return dir

@route(PREFIX + '/getFolders')
def getFolders():
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L("oc_title_folders"))
  element = XML.ElementFromURL(makeURL("getMusicFolders.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, "{http://subsonic.org/restapi}musicFolder"):
    title       = item.get("name")
    id          = item.get("id")
    key         = PREFIX + '/getArtistFolder/' + id
    dir.add(DirectoryObject(title=title, key=key))
    #return dir
  return dir

@route(PREFIX + '/getArtistFolder/{folderID}')
def getArtistFolder(folderID):
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L("oc_title_artists"))
  element = XML.ElementFromURL(makeURL("getIndexes.view", musicFolderId=folderID), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, ARTIST):
    title       = item.get("name")
    id          = item.get("id")
    key         = PREFIX + '/getArtist/' + id
    artistThumb = PREFIX + '/getArtistThumb/' + id
    dir.add(DirectoryObject(title=title, key=key, thumb=Callback(getArtistThumb, artistID=id)))
    #return dir
  return dir

#create a menu listing all artists
@route(PREFIX + '/getArtists')
def getArtists():
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  dir = ObjectContainer(title1=L("oc_title_artists"))
  element = XML.ElementFromURL(makeURL("getIndexes.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, ARTIST):
    title       = item.get("name")
    id          = item.get("id")
    key         = PREFIX + '/getArtist/' + id
    artistThumb = PREFIX + '/getArtistThumb/' + id
    dir.add(DirectoryObject(title=title, key=key, thumb=Callback(getArtistThumb, artistID=id)))
    #return dir
  return dir

@route(PREFIX + '/getArtistThumb/{artistID}')
def getArtistThumb(artistID):
  element = XML.ElementFromURL(makeURL("getArtistInfo.view", id=artistID), cacheTime=CACHE_INTERVAL)
  largeImageUrl = R(NOART)
  liu = element.xpath('./media:artistInfo/media:largeImageUrl/text()', namespaces=NS)
  if liu:
    largeImageUrl = liu[0]
    return HTTP.Request(largeImageUrl).content
  else:
    return largeImageUrl

#create a menu with all albums for selected artist
@route(PREFIX + '/getArtist/{artistID}')
def getArtist(artistID):
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  element = XML.ElementFromURL(makeURL("getMusicDirectory.view", id=artistID), cacheTime=CACHE_INTERVAL)
  artistName = element.find(DIRECTORY).get("name")
  dir = ObjectContainer(title1=artistName)
  #artistKey = PREFIX + '/getArtist/' + artistID
  #artist = ArtistObject(title="test", key=artistKey, rating_key=artistID, thumb=Callback(getArtistThumb, artistID=artistID))
  #dir.add(artist)
  for item in searchElementTree(element, CHILD):
    title       = item.get("title")
    id          = item.get("id")
    coverArt    = item.get("coverArt")
    key         = PREFIX + '/getAlbum/' + id
    thumbURL    = makeURL("getCoverArt.view", id=coverArt) if coverArt else R(NOART)
    #dir.add(AlbumObject(title=title, key=key, rating_key=id, thumb=thumbURL))
    dir.add(DirectoryObject(title=title, key=key, thumb=thumbURL))
    #dir.add(AlbumObject(title=title, key=Callback(getAlbum, albumID=id), rating_key=id, thumb=thumbURL))
  return dir

#create a menu with all songs for selected album
@route(PREFIX + '/getAlbum/{albumID}')
def getAlbum(albumID):
  if not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  
  #populate the track listing
  element = XML.ElementFromURL(makeURL("getMusicDirectory.view", id=albumID), cacheTime=CACHE_INTERVAL)
  albumName = element.find(DIRECTORY).get("name")
  dir = ObjectContainer(title1=albumName)
  for item in searchElementTree(element, CHILD):
    artist      = item.get("artist")
    album       = item.get("album")
    title       = item.get("title")
    id          = item.get("id")
    try:
      track     = int(item.get("track"))
    except:
      track     = 1
    genre       = item.get("genre")
    rating_key  = id
    duration = 1000 * int(item.get("duration"))
    url = makeURL("stream.view", id=id, format=container)
    coverArt = item.get("coverArt")
    if coverArt:
      thumbnail = makeURL("getCoverArt.view", id=coverArt)
    else:
      thumbnail = R(NOART)
    Log("AAAARRRGGGGHHHHHHH")
    Log(thumbnail)
    dir.add(TrackObject(
      artist=artist, 
      album=album, 
      title=title, 
      duration=duration, 
      key=id, #might need to change this line eventually to return metadata instead of playing track
      rating_key=rating_key,
      thumb=thumbnail,
      art=thumbnail,
      index=track,
      genres=[genre],
      items = [
        MediaObject(
          parts = [
            PartObject(key=Callback(playAudio, url=url, ext=container))
          ],
          container = container,
          audio_codec = audio_codec,
          audio_channels = 2,
          platforms=[]
        )
      ]))
  return dir
  
@route(PREFIX + '/getAlbum/{albumID}/{songID}')
def getSong(albumID, songID):
        return True

#play an audio track (copied this function from the Plex Shoutcast channel)
def playAudio(url):
	content = HTTP.Request(url, cacheTime=0).content
	if content:
		return content
	else:
		raise Ex.MediaNotAvailable
    
#construct a http GET request from a view name and parameters
def makeURL(view, **parameters):
  url = Prefs['server']
  url += "rest/" + view + "?"
  parameters['u'] = Prefs['username']
  parameters['p'] = "enc:" + binascii.hexlify(Prefs['password'])
  parameters['v'] = SUBSONIC_API_VERSION
  parameters['c'] = SUBSONIC_CLIENT
  for param in parameters:
    url += param + "=" + parameters[param] + "&"
  return url

#recursively search etree and return list with all the elements that match  
def searchElementTree(element, search):
  matches = element.findall(search)
  if len(element):
    for e in list(element):
      matches += searchElementTree(e, search)
  return matches

#check that media server is accessible
def serverStatus():
  #check that Preferences have been set
  if not (Prefs['username'] and Prefs['password'] and Prefs['server']):
    return False
  #try to ping server with credentials
  elif XML.ElementFromURL(makeURL("ping.view"), cacheTime=None).get("status") != "ok":
    return False
  #connection is successful, return True and proceed!
  else:
    return True
    
#Plex calls this functions anytime Prefs are changed
def ValidatePrefs():
  if Prefs['server'][-1] != '/':
    return ObjectContainer(header=L("msg_validate_slash_head"), message=L("msg_validate_slash_body"))
  elif not serverStatus():
    return ObjectContainer(header=L("msg_connect_head"), message=L("msg_connext_body"))
