import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
import os
import unicodedata
from xml.dom.minidom import parse

__settings__ = xbmcaddon.Addon(id='plugin.video.SageTV')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')

# SageTV recording Directories for path replacement
sage_rec = __settings__.getSetting("sage_rec")
sage_unc = __settings__.getSetting("sage_unc")

# SageTV URL based on user settings
strUrl = 'http://' + __settings__.getSetting("sage_user") + ':' + __settings__.getSetting("sage_pass") + '@' + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")

def CATEGORIES():
 
        addDir('All Shows', strUrl + '/sage/Recordings?xml=yes',2,'icon.png')
        req = urllib.urlopen(strUrl + '/sage/Recordings?xml=yes')
        content = parse(req)
        uniqueListOfShowTitles = []
        for showlist in content.getElementsByTagName('show'):
          strTitle = ''
          for shownode in showlist.childNodes:
            # Get the title of the show
            if shownode.nodeName == 'title':
              strTitle = shownode.toxml()
              strTitle = strTitle.replace('<title>','')
              strTitle = strTitle.replace('</title>','')
              strTitle = strTitle.replace('&amp;','&')
              strTitle = strTitle.replace('&quot;','"')
              strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
              if strTitle not in uniqueListOfShowTitles:
                uniqueListOfShowTitles.append(strTitle)

        uniqueListOfShowTitles.sort()
        for strTitle in uniqueListOfShowTitles:
            urlToShowEpisodes = strUrl + '/sage/Search?searchType=TVFiles&SearchString=' + urllib2.quote(strTitle.encode("utf8")) + '&DVD=on&sort2=airdate_asc&TimeRange=0&pagelen=100&sort1=title_asc&filename=&Video=on&search_fields=title&xml=yes'
            print "ADDING strTitle=" + strTitle + "; urlToShowEpisodes=" + urlToShowEpisodes
            addDir(strTitle, urlToShowEpisodes,2,'icon.png')

def VIDEOLINKS(url,name):
        #Videolinks gets called immediately after adddir, so the timeline is categories, adddir, and then videolinks
        #Videolinks then calls addlink in a loop
        #This code parses the xml link
        req = urllib.urlopen(url)
        content = parse(req)     
        for showlist in content.getElementsByTagName('show'):
          strTitle = ''
          strEpisode = ''
          strDescription = ''
          strGenre = ''
          strAirdate = ''
          strMediaFileID = ''
          for shownode in showlist.childNodes:
            # Get the title of the show
            if shownode.nodeName == 'title':
              strTitle = shownode.toxml()
              strTitle = strTitle.replace('<title>','')
              strTitle = strTitle.replace('</title>','')
              strTitle = strTitle.replace('&amp;','&')
            # Get the episode name
            if shownode.nodeName == 'episode':
              strEpisode = shownode.toxml()
              strEpisode = strEpisode.replace('<episode>','')
              strEpisode = strEpisode.replace('</episode>','')
              strEpisode = strEpisode.replace('&amp;','&')
            # Get the show description
            if shownode.nodeName == 'description':
              strDescription = shownode.toxml()
              strDescription = strDescription.replace('<description>','')
              strDescription = strDescription.replace('</description>','')
              strDescription = strDescription.replace('&amp;','&')
            # Get the category to use for genre
            if shownode.nodeName == 'category':
              strGenre = shownode.toxml()
              strGenre = strGenre.replace('<category>','')
              strGenre = strGenre.replace('</category>','')
              strGenre = strGenre.replace('&amp;','&')
            # Get the airdate to use for Aired
            if shownode.nodeName == 'originalAirDate':
              strAirdate = shownode.toxml()
              strAirdate = strAirdate.replace('<originalAirDate>','')
              strAirdate = strAirdate.replace('</originalAirDate>','')
              strAirdate = strAirdate[:10]
              # now that we have the title, episode, genre and description, create a showname string depending on which ones you have
              # if there is no episode name use the description in the title
            if len(strEpisode) == 0:
              strShowname = strTitle+' - '+strDescription
              strPlot = strDescription
              # else if there is an episode use that
            elif len(strEpisode) > 0:
              if name == 'All Shows' or name == 'Sports': 
                strShowname = strTitle+' - '+strEpisode
              elif name != 'All Shows' and name != 'Sports':
                strShowname = strEpisode
              strPlot = strDescription
            if shownode.nodeName == 'airing':
              for shownode1 in shownode.childNodes:
                if shownode1.nodeName == 'mediafile':
                  strMediaFileID = shownode1.getAttribute('sageDbId')
                  for shownode2 in shownode1.childNodes:
                    if shownode2.nodeName == 'segmentList':
                      shownode3 =  shownode2.childNodes[1]
                      strFilepath = shownode3.getAttribute('filePath')
                      addLink(strShowname,strFilepath.replace(sage_rec, sage_unc),strPlot,'',strGenre,strAirdate,strTitle,strMediaFileID)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def addLink(name,url,plot,iconimage,genre,airdate,showtitle,fileid):
        ok=True
        liz=xbmcgui.ListItem(name)
        strDelete = strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + fileid
        liz.addContextMenuItems([('Delete Show', 'PlayMedia(' + strDelete + ')',)])
        datesplit = airdate.split('-')
        try:
            date = datesplit[2]+'.'+datesplit[1]+'.'+datesplit[0]
        except:
            date = "01.01.1900"
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": date, "aired": airdate, "TVShowTitle": showtitle } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name)
        liz.setInfo(type="video", infoLabels={ "Title": name } )
        liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
        liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
        
              
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
        print ""
        CATEGORIES()
       
elif mode==1:
        print ""+url
        INDEX(url)
        
elif mode==2:
        print ""+url
        VIDEOLINKS(url,name)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.setContent(int(sys.argv[1]),'episodes')
xbmcplugin.endOfDirectory(int(sys.argv[1]))