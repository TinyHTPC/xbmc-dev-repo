# Initializes and launches Couchpotato V2, Sickbeard and Headphones

from xml.dom.minidom import parseString
from lib.configobj import ConfigObj
import os
import subprocess
import hashlib
import platform
import xbmc
import xbmcaddon
import xbmcvfs
import time
import xbmcgui
import sys
import socket
import fcntl
import struct

import signal

# helper functions
# ----------------


def create_dir(dirname):
    if not xbmcvfs.exists(dirname):
        xbmcvfs.mkdirs(dirname)

def check_connection():
        ifaces = ['eth0','eth1','wlan0','wlan1','wlan2','wlan3']
        connected = []
        i = 0
        for ifname in ifaces:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                socket.inet_ntoa(fcntl.ioctl(
                        s.fileno(),
                        0x8915,  # SIOCGIFADDR
                        struct.pack('256s', ifname[:15])
                )[20:24])
                connected.append(ifname)
                print "%s is connected" % ifname
            except:
                print "%s is not connected" % ifname
            i += 1
        return connected

def ensure_dir(f):
    print "Checking for location: "+f
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
	print "Not Found! Creating: "+d

def media_link(link, dest):
    print "Checking for location: "+link
    rm = "rm "+link
    ln = "ln -s "+dest+" "+link
    if not os.path.exists(link):
        subprocess.check_output(ln, shell=True)
	print "Not Found! Creating: "+link
    elif os.path.exists(link):
	print "Link Already Found!"
        subprocess.check_output(rm, shell=True)
	print "Removing: "+link
        subprocess.check_output(ln, shell=True)
	print "Creating: "+link

# define some things that we're gonna need, mainly paths
# ------------------------------------------------------

#Get host IP:
connected_ifaces = check_connection()
if len(connected_ifaces) == 0:
    print 'not connected to any network'
    hostIP = "on Port"
else:
    GetIP = ([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
    hostIP = ' on '+GetIP
    print hostIP

#Create Strings for notifications:
started   = 'Service started'+hostIP
waiting   = 'Looking for Media download folders...'
disabled  = 'Service disabled for this session'
SBport  = ':8082'
CPport  = ':8083'
HPport  = ':8084'

# addon
__addon__             = xbmcaddon.Addon(id='service.downloadmanager.InternetPVR')
__addonpath__         = xbmc.translatePath(__addon__.getAddonInfo('path'))
__addonhome__         = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__icon__              = __addon__.getAddonInfo('icon')
xbmcUdat              = os.path.expanduser("~/.xbmc/userdata")

# settings
pDefaultSuiteSettings = xbmc.translatePath(__addonpath__ + '/settings-default.xml')
pSuiteSettings        = xbmc.translatePath(__addonhome__ + 'settings.xml')
pXbmcSettings         = os.path.join(xbmcUdat, "guisettings.xml")
pSickBeardSettings    = xbmc.translatePath(__addonhome__ + 'sickbeard.ini')
pCouchPotatoServerSettings  = xbmc.translatePath(__addonhome__ + 'couchpotatoserver.ini')
pHeadphonesSettings   = xbmc.translatePath(__addonhome__ + 'headphones.ini')

# directories
##Read from Transmission Settings

# pylib
pPylib                = xbmc.translatePath(__addonpath__ + '/resources/lib')

# service commands
sickBeard             = ['python', xbmc.translatePath(__addonpath__ + '/resources/SickBeard/SickBeard.py'),
                         '--daemon', '--datadir', __addonhome__, '--config', pSickBeardSettings]
couchPotatoServer     = ['python', xbmc.translatePath(__addonpath__ + '/resources/CouchPotatoServer/CouchPotato.py'),
                         '--daemon', '--pid_file', xbmc.translatePath(__addonhome__ + 'couchpotato.pid'),
                         '--config_file', pCouchPotatoServerSettings]
headphones            = ['python', xbmc.translatePath(__addonpath__ + '/resources/Headphones/Headphones.py'),
                         '-d', '--datadir', __addonhome__, '--config', pHeadphonesSettings]

# create directories and settings if missing
# -----------------------------------------------

sbfirstLaunch = not xbmcvfs.exists(pSickBeardSettings)
cpfirstLaunch = not xbmcvfs.exists(pCouchPotatoServerSettings)
hpfirstLaunch = not xbmcvfs.exists(pHeadphonesSettings)
if sbfirstLaunch or cpfirstLaunch or hpfirstLaunch:
    xbmc.log('SickPotatoHead: First launch, creating directories', level=xbmc.LOGDEBUG)
    create_dir(__addonhome__)

# create the settings file if missing
if not xbmcvfs.exists(pSuiteSettings):
    xbmcvfs.copy(pDefaultSuiteSettings, pSuiteSettings)

# read addon and xbmc settings
# ----------------------------

pTransmission_Addon_Settings  = os.path.expanduser("~/.xbmc/userdata/addon_data/service.downloadmanager.transmission/settings.xml")
pTransmission_Settings_New    = os.path.expanduser("~/.xbmc/userdata/addon_data/service.downloadmanager.transmission/settings2.xml")
pTransmission_DIR             = os.path.expanduser("~/.xbmc/addons/service.downloadmanager.transmission")
pTransmission_Stop            = os.path.expanduser("~/.xbmc/addons/service.downloadmanager.transmission/bin/transmission.stop")
pTransmission_Start           = os.path.expanduser("~/.xbmc/addons/service.downloadmanager.transmission/bin/transmission.start")

# Transmission-Daemon
transauth = False
try:
    transmissionaddon = xbmcaddon.Addon(id='service.downloadmanager.transmission')
    transauth = (transmissionaddon.getSetting('TRANSMISSION_AUTH').lower() == 'true')
    transdl = (transmissionaddon.getSetting('TRANSMISSION_DL_DIR').decode('utf-8'))
    transinc = (transmissionaddon.getSetting('TRANSMISSION_INC_DIR').decode('utf-8'))
    transwatch = (transmissionaddon.getSetting('TRANSMISSION_WATCH_DIR').decode('utf-8'))

    if transauth:
        xbmc.log('InternetPVR: Transmission Authentication Enabled', level=xbmc.LOGDEBUG)
        transuser = (transmissionaddon.getSetting('TRANSMISSION_USER').decode('utf-8'))
        if transuser == '':
            transuser = None
        transpwd = (transmissionaddon.getSetting('TRANSMISSION_PWD').decode('utf-8'))
        if transpwd == '':
            transpwd = None
    else:
        xbmc.log('InternetPVR: Transmission Authentication Not Enabled', level=xbmc.LOGDEBUG)

except Exception, e:
    xbmc.log('InternetPVR: Transmission Settings are not present', level=xbmc.LOGNOTICE)
    xbmc.log(str(e), level=xbmc.LOGNOTICE)
    pass

# InternetPVR-Suite
user = (__addon__.getSetting('InternetPVR_USER').decode('utf-8'))
pwd = (__addon__.getSetting('InternetPVR_PWD').decode('utf-8'))
host = (__addon__.getSetting('InternetPVR_IP'))
sickbeard_launch = (__addon__.getSetting('SICKBEARD_LAUNCH').lower() == 'true')
couchpotato_launch = (__addon__.getSetting('COUCHPOTATO_LAUNCH').lower() == 'true')
headphones_launch = (__addon__.getSetting('HEADPHONES_LAUNCH').lower() == 'true')
simplemode = (__addon__.getSetting('InternetPVR_MODE').lower() == 'true')
sickbeard_watch_dir = (__addon__.getSetting('TVSHOW_DIR').decode('utf-8'))
couchpotato_watch_dir = (__addon__.getSetting('MOVIES_DIR').decode('utf-8'))
headphones_watch_dir = (__addon__.getSetting('MUSIC_DIR').decode('utf-8'))
transmission_dl_dir = (__addon__.getSetting('TRANSMISSION_DL_DIR').decode('utf-8'))

# Set Downloads directories
pHomeDownloadsDir              = transmission_dl_dir
pInternetPVRComplete           = transmission_dl_dir + "complete"
pInternetPVRCompleteTV         = transmission_dl_dir + "complete/tvshows"
pInternetPVRCompleteMov        = transmission_dl_dir + "complete/movies"
pInternetPVRCompleteMus        = transmission_dl_dir + "complete/music"
#pInternetPVRWatchDir           = transmission_dl_dir + "torrents"

# XBMC
fXbmcSettings                 = open(pXbmcSettings, 'r')
data                          = fXbmcSettings.read()
fXbmcSettings.close()
xbmcSettings                  = parseString(data)
xbmcServices                  = xbmcSettings.getElementsByTagName('services')[0]
xbmcPort                      = xbmcServices.getElementsByTagName('webserverport')[0].firstChild.data
try:
    xbmcUser                      = xbmcServices.getElementsByTagName('webserverusername')[0].firstChild.data
except StandardError:
    xbmcUser                      = ''
try:
    xbmcPwd                       = xbmcServices.getElementsByTagName('webserverpassword')[0].firstChild.data
except StandardError:
    xbmcPwd                       = ''

# prepare execution environment
# -----------------------------
parch                         = platform.machine()
pnamemapper                   = xbmc.translatePath(pPylib + '/Cheetah/_namemapper.so')
petree                        = xbmc.translatePath(pPylib + '/lxml/etree.so')
pobjectify                    = xbmc.translatePath(pPylib + '/lxml/objectify.so')
punrar                        = xbmc.translatePath(__addonpath__ + '/bin/unrar')

xbmc.log('SickPotatoHead: ' + parch + ' architecture detected', level=xbmc.LOGDEBUG)

if parch.startswith('arm'):
    parch = 'arm'

if not xbmcvfs.exists(pnamemapper):
    try:
        fnamemapper                   = xbmc.translatePath(pPylib + '/multiarch/_namemapper.so.' + parch)
        xbmcvfs.copy(fnamemapper, pnamemapper)
        xbmc.log('SickPotatoHead: Copied _namemapper.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('SickPotatoHead: Error Copying _namemapper.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(petree):
    try:
        fetree                        = xbmc.translatePath(pPylib + '/multiarch/etree.so.' + parch)
        xbmcvfs.copy(fetree, petree)
        xbmc.log('SickPotatoHead: Copied etree.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('SickPotatoHead: Error Copying etree.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(pobjectify):
    try:
        fobjectify                    = xbmc.translatePath(pPylib + '/multiarch/objectify.so.' + parch)
        xbmcvfs.copy(fobjectify, pobjectify)
        xbmc.log('SickPotatoHead: Copied objectify.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('SickPotatoHead: Error Copying objectify.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(punrar):
    try:
        funrar                        = xbmc.translatePath(pPylib + '/multiarch/unrar.' + parch)
        xbmcvfs.copy(funrar, punrar)
        os.chmod(punrar, 0755)
        xbmc.log('AUDO: Copied unrar for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying unrar for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

os.environ['PYTHONPATH'] = str(os.environ.get('PYTHONPATH')) + ':' + pPylib

# Check directories still exist
dlDIR  = not os.path.exists(pHomeDownloadsDir)
print "Checking if Downloads DIR has been removed: "+pHomeDownloadsDir+"..."
print dlDIR
dialog = xbmcgui.Dialog()
while (dlDIR != ""):
	dlDIR  = not os.path.exists(pHomeDownloadsDir)
	if dlDIR:
		promptstart = dialog.yesno(__addonname__, "Could not find your Download directory.", "Check that your location settings are correct.", "[B]Would you like to disable "+__addonname__+" for this session?[/B]")
		if promptstart:
			dialog.ok(__addonname__, __addonname__+" has been disabled for this session", "", "[B]To use "+__addonname__+", restart XBMC[/B]")
			xbmc.executebuiltin('XBMC.Notification('+ __addonname__ +','+ disabled +',5000,'+ __icon__ +')')
			sys.exit("InternetPVR not Started")
		else:
			xbmc.executebuiltin('XBMC.Notification('+ __addonname__ +','+ waiting +',5000,'+ __icon__ +')')
		time.sleep(20)
	else:
		#xbmc.executebuiltin('XBMC.Notification('+ __addonname__ +','+ started +',5000,'+ __icon__ +')')
		break

# Create media directories if missing
ensure_dir(sickbeard_watch_dir+"/*")
ensure_dir(couchpotato_watch_dir+"/*")
ensure_dir(headphones_watch_dir+"/*")
ensure_dir(pInternetPVRCompleteTV+"/*")
ensure_dir(pInternetPVRCompleteMov+"/*")
ensure_dir(pInternetPVRCompleteMus+"/*")

# Edit Transmission settings and restart.
print "Edit Transmission settings and restart."
infile = open(pTransmission_Addon_Settings)
outfile = open(pTransmission_Settings_New, 'w')

replacements = {transdl:transmission_dl_dir+'complete', transinc:transmission_dl_dir+'incoming'}

for line in infile:
    for src, target in replacements.iteritems():
        line = line.replace(src, target)
    outfile.write(line)
infile.close()
outfile.close()

from os import remove
from shutil import move

remove(pTransmission_Addon_Settings)
move(pTransmission_Settings_New, pTransmission_Addon_Settings)


print "Restarting Transmission..."
subprocess.Popen("chmod -R +x " + pTransmission_DIR + "/bin/*" , shell=True, close_fds=True)
subprocess.Popen(pTransmission_Stop, shell=True, close_fds=True)
time.sleep(15)
subprocess.Popen(pTransmission_Start, shell=True, close_fds=True)
time.sleep(1)

# Execution Services:
# -------------------
# SickBeard start
try:
    # write SickBeard settings
    # ------------------------
    sickBeardConfig = ConfigObj(pSickBeardSettings, create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['General'] = {}
    defaultConfig['General']['launch_browser']      = '0'
    defaultConfig['General']['version_notify']      = '0'
    defaultConfig['General']['web_port']            = '8082'
    defaultConfig['General']['web_host']            = host
    defaultConfig['General']['web_username']        = user
    defaultConfig['General']['web_password']        = pwd
    defaultConfig['General']['cache_dir']           = __addonhome__ + 'sbcache'
    defaultConfig['General']['log_dir']             = __addonhome__ + 'logs'
    defaultConfig['XBMC'] = {}
    defaultConfig['XBMC']['use_xbmc']               = '1'
    defaultConfig['XBMC']['xbmc_host']              = 'localhost:' + xbmcPort
    defaultConfig['XBMC']['xbmc_username']          = xbmcUser
    defaultConfig['XBMC']['xbmc_password']          = xbmcPwd

    if simplemode:
        defaultConfig['General']['torrent_method']        = 'transmission'
        defaultConfig['General']['naming_pattern']        = 'Season %0S/%S.N.S%0SE%0E.%Q.N-%RG'
        defaultConfig['General']['process_automatically'] = '1'
        defaultConfig['General']['tv_download_dir']       = pInternetPVRCompleteTV
        defaultConfig['General']['metadata_xbmc_12plus']  = '0|0|0|0|0|0|0|0|0|0'
        defaultConfig['General']['keep_processed_dir']    = '0'
        defaultConfig['General']['use_banner']            = '1'
        defaultConfig['General']['rename_episodes']       = '1'
        defaultConfig['General']['naming_ep_name']        = '0'
        defaultConfig['General']['naming_use_periods']    = '1'
        defaultConfig['General']['naming_sep_type']       = '1'
        defaultConfig['General']['naming_ep_type']        = '1'
        defaultConfig['General']['root_dirs']             = '0|' + sickbeard_watch_dir
        defaultConfig['General']['naming_custom_abd']     = '0'
        defaultConfig['TORRENT'] = {}
        defaultConfig['TORRENT']['torrent_path']          = pInternetPVRCompleteTV
        defaultConfig['TORRENT']['torrent_host']          = 'http://localhost:9091/'
        defaultConfig['EZRSS'] = {}
        defaultConfig['EZRSS']['ezrss']                   = '1'
        defaultConfig['PUBLICHD'] = {}
        defaultConfig['PUBLICHD']['publichd']             = '1'
        defaultConfig['KAT'] = {}
        defaultConfig['KAT']['kat']                       = '1'
        defaultConfig['THEPIRATEBAY'] = {}
        defaultConfig['THEPIRATEBAY']['thepiratebay']     = '1'
        defaultConfig['XBMC']['xbmc_notify_ondownload']   = '1'
        defaultConfig['XBMC']['xbmc_notify_onsnatch']     = '1'
        defaultConfig['XBMC']['xbmc_update_library']      = '1'
        defaultConfig['XBMC']['xbmc_update_full']         = '1'

    if transauth:
        defaultConfig['TORRENT'] = {}
        defaultConfig['TORRENT']['torrent_username']         = transuser
        defaultConfig['TORRENT']['torrent_password']         = transpwd
        defaultConfig['TORRENT']['torrent_path']             = pInternetPVRCompleteTV
        defaultConfig['TORRENT']['torrent_host']             = 'http://localhost:9091/'

    sickBeardConfig.merge(defaultConfig)
    sickBeardConfig.write()

    # launch SickBeard
    # ----------------
    if sickbeard_launch:
        xbmc.log('SickPotatoHead: Launching SickBeard...', level=xbmc.LOGDEBUG)
        subprocess.call(sickBeard, close_fds=True)
        xbmc.log('SickPotatoHead: ...done', level=xbmc.LOGDEBUG)
        xbmc.executebuiltin('XBMC.Notification(SickBeard,'+ started + SBport +',5000,'+ __icon__ +')')
except Exception, e:
    xbmc.log('SickPotatoHead: SickBeard exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# SickBeard end

# CouchPotatoServer start
try:
    # empty password hack
    if pwd == '':
        md5pwd = ''
    else:
        #convert password to md5
        md5pwd = hashlib.md5(str(pwd)).hexdigest()

    # write CouchPotatoServer settings
    # --------------------------
    couchPotatoServerConfig = ConfigObj(pCouchPotatoServerSettings, create_empty=True, list_values=False)
    defaultConfig = ConfigObj()
    defaultConfig['core'] = {}
    defaultConfig['core']['username']               = user
    defaultConfig['core']['password']               = md5pwd
    defaultConfig['core']['port']                   = '8083'
    defaultConfig['core']['launch_browser']         = '0'
    defaultConfig['core']['host']                   = host
    defaultConfig['core']['data_dir']               = __addonhome__
    defaultConfig['core']['show_wizard']            = '0'
    defaultConfig['core']['debug']                  = '0'
    defaultConfig['core']['development']            = '0'
    defaultConfig['updater'] = {}
    defaultConfig['updater']['enabled']             = '0'
    defaultConfig['updater']['notification']        = '0'
    defaultConfig['updater']['automatic']           = '0'
    defaultConfig['xbmc'] = {}
    defaultConfig['xbmc']['enabled']                = '1'
    defaultConfig['xbmc']['host']                   = 'localhost:' + xbmcPort
    defaultConfig['xbmc']['username']               = xbmcUser
    defaultConfig['xbmc']['password']               = xbmcPwd

    if simplemode:
        defaultConfig['xbmc'] = {}
        defaultConfig['xbmc']['xbmc_update_library']      = '1'
        defaultConfig['xbmc']['force_full_scan']          = '1'
        defaultConfig['xbmc']['on_snatch']                = '1'
        defaultConfig['xbmc']['xbmc_notify_ondownload']   = '1'
        defaultConfig['blackhole'] = {}
        defaultConfig['blackhole']['directory']           = transwatch
        defaultConfig['blackhole']['use_for']             = 'torrent'
        defaultConfig['blackhole']['enabled']             = '0'
        defaultConfig['renamer'] = {}
        defaultConfig['renamer']['enabled']               = '1'
        defaultConfig['renamer']['from']                  = pInternetPVRCompleteMov
        defaultConfig['renamer']['separator']             = '.'
        defaultConfig['renamer']['cleanup']               = '0'
        defaultConfig['renamer']['file_action']           = 'move'
        defaultConfig['subtitle'] = {}
        defaultConfig['subtitle']['languages']            = 'en'
        defaultConfig['subtitle']['enabled']              = '1'
        defaultConfig['nzbindex'] = {}
        defaultConfig['nzbindex']['enabled']              = '0'
        defaultConfig['mysterbin'] = {}
        defaultConfig['mysterbin']['enabled']             = '0'
        defaultConfig['core'] = {}
        defaultConfig['core']['api_key']                  = 'f181f1fff3c34ba5bc27b0e1c846cfe4'
        defaultConfig['core']['permission_folder']        = '0644'
        defaultConfig['core']['permission_file']          = '0644'
        defaultConfig['core']['port']                     = '8083'
        defaultConfig['core']['show_wizard']              = '0'
        defaultConfig['searcher'] = {}
        defaultConfig['searcher']['preferred_method']     = 'torrent'
        defaultConfig['searcher']['required_words']       = '720p, 1080p'
        defaultConfig['searcher']['preferred_words']      = 'YIFY, x264, BrRip'
        defaultConfig['manage'] = {}
        defaultConfig['manage']['startup_scan']           = '0'
        defaultConfig['manage']['library_refresh_interval'] = '10'
        defaultConfig['manage']['enabled']                = '1'
        defaultConfig['manage']['library']                = couchpotato_watch_dir
        defaultConfig['transmission'] = {}
        defaultConfig['transmission']['enabled']          = '1'
        defaultConfig['transmission']['directory']        = pInternetPVRCompleteMov
        defaultConfig['transmission']['host']             = 'localhost:9091'
        defaultConfig['newznab'] = {}
        defaultConfig['newznab']['enabled']               = '0'
        defaultConfig['yify'] = {}
        defaultConfig['yify']['enabled']                  = '1'
        defaultConfig['yify']['seed_time']                = '0'
        defaultConfig['yify']['seed_ratio']               = '0'
        defaultConfig['yify']['extra_score']              = '30000'
        defaultConfig['kickasstorrents'] = {}
        defaultConfig['kickasstorrents']['enabled']       = 'True'
        defaultConfig['kickasstorrents']['seed_time']     = '0'
        defaultConfig['kickasstorrents']['seed_ratio']    = '0'
        defaultConfig['torrentz'] = {}
        defaultConfig['torrentz']['enabled']              = 'True'
        defaultConfig['torrentz']['verified_only']        = 'True'
        defaultConfig['torrentz']['seed_time']            = '0'
        defaultConfig['torrentz']['seed_ratio']           = '0'

    if transauth:
        defaultConfig['transmission'] = {}
        defaultConfig['transmission']['username']         = transuser
        defaultConfig['transmission']['password']         = transpwd
        defaultConfig['transmission']['directory']        = pInternetPVRCompleteMov
        defaultConfig['transmission']['host']             = 'localhost:9091'

    couchPotatoServerConfig.merge(defaultConfig)
    couchPotatoServerConfig.write()

    # launch CouchPotatoServer
    # ------------------
    if couchpotato_launch:
        xbmc.log('SickPotatoHead: Launching CouchPotatoServer...', level=xbmc.LOGDEBUG)
        subprocess.call(couchPotatoServer, close_fds=True)
        xbmc.log('SickPotatoHead: ...done', level=xbmc.LOGDEBUG)
        xbmc.executebuiltin('XBMC.Notification(CouchPotatoServer,'+ started + CPport +',5000,'+ __icon__ +')')
except Exception, e:
    xbmc.log('SickPotatoHead: CouchPotatoServer exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# CouchPotatoServer end

# Headphones start
try:
    # write Headphones settings
    # -------------------------
    headphonesConfig = ConfigObj(pHeadphonesSettings, create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['General'] = {}
    defaultConfig['General']['launch_browser']            = '0'
    defaultConfig['General']['http_port']                 = '8084'
    defaultConfig['General']['http_host']                 = host
    defaultConfig['General']['http_username']             = user
    defaultConfig['General']['http_password']             = pwd
    defaultConfig['General']['check_github']              = '0'
    defaultConfig['General']['check_github_on_startup']   = '0'
    defaultConfig['General']['cache_dir']                 = __addonhome__ + 'hpcache'
    defaultConfig['General']['log_dir']                   = __addonhome__ + 'logs'
    defaultConfig['XBMC'] = {}
    defaultConfig['XBMC']['xbmc_enabled']                 = '1'
    defaultConfig['XBMC']['xbmc_host']                    = 'localhost:' + xbmcPort
    defaultConfig['XBMC']['xbmc_username']                = xbmcUser
    defaultConfig['XBMC']['xbmc_password']                = xbmcPwd

    if simplemode:
        defaultConfig['XBMC']['xbmc_update']                  = '1'
        defaultConfig['XBMC']['xbmc_notify']                  = '1'
        defaultConfig['General']['music_dir']                 = headphones_watch_dir
        defaultConfig['General']['destination_dir']           = headphones_watch_dir
        defaultConfig['General']['prefer_torrents']           = '1'
        defaultConfig['General']['torrentblackhole_dir']      = transwatch
        defaultConfig['General']['download_torrent_dir']      = pInternetPVRCompleteMus
        defaultConfig['General']['move_files']                = '1'
        defaultConfig['General']['rename_files']              = '1'
        defaultConfig['General']['correct_metadata']          = '1'
        defaultConfig['General']['cleanup_files']             = '1'
        defaultConfig['General']['folder_permissions']        = '0644'
        defaultConfig['General']['torrent_downloader']        = '1'
        defaultConfig['General']['api_enabled']               = '1'
        defaultConfig['General']['api_key']                   = 'baf90d3054d3707e2c083d33137ba6eb'
        defaultConfig['General']['move_files']                = '1'
        defaultConfig['General']['piratebay']                 = '1'
        defaultConfig['General']['kat']                       = '1'
        defaultConfig['General']['isohunt']                   = '1'
        defaultConfig['General']['kat']                       = '1'
        defaultConfig['General']['mininova']                  = '1'
        defaultConfig['General']['piratebay']                 = '1'
        defaultConfig['Transmission'] = {}
        defaultConfig['Transmission']['transmission_host']    = 'http://localhost:9091'


    if transauth:
        defaultConfig['Transmission'] = {}
        defaultConfig['Transmission']['transmission_username'] = transuser
        defaultConfig['Transmission']['transmission_password'] = transpwd
        defaultConfig['Transmission']['transmission_host']     = 'http://localhost:9091'

    headphonesConfig.merge(defaultConfig)
    headphonesConfig.write()

    # launch Headphones
    # -----------------
    if headphones_launch:
        xbmc.log('SickPotatoHead: Launching Headphones...', level=xbmc.LOGDEBUG)
        subprocess.call(headphones, close_fds=True)
        xbmc.log('SickPotatoHead: ...done', level=xbmc.LOGDEBUG)
        xbmc.executebuiltin('XBMC.Notification(Headphones,'+ started + HPport +',5000,'+ __icon__ +')')
except Exception, e:
    xbmc.log('SickPotatoHead: Headphones exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# Headphones end
