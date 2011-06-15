"""The application's Globals object"""

class Globals(object):

    """Globals acts as a container for objects available throughout the
    life of the application
    """
    
    

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        self.NEW_SHP_SCAN_DIR = '/mol-data/new/animalia/species'
        #self.TILE_DIR = "/ftp/tile/animalia/species"
        self.TILE_DIR = "/tmp/range/tile"
        self.RANGESHP_DIR = "/mol-data/range/shp"
        self.ECOTILE_DIR = "/tmp/ecoregion/tile"
        self.ECOSHP_DIR = "/mol-data/ecoregion/shp"
        self.PATILE_DIR = "/tmp/pa/tile"
        self.PASHP_DIR = "/mol-data/pa/shp"
        self.OVERVIEW_DIR = "/tmp/overviews"
        self.ERR_DIR = "/mol-data/range/error/"
        self.SRC_DIR = "/mol-data/range/new/"
        self.DST_DIR = "/mol-data/range/shp/"
        self.MAP_XML = "/mol-data/tile/mapfile.xml"
        self.ECO_MAP_XML = "/mol-data/ecoregion/tile/mapfile.xml"
        #self.GAE_URL = "http://localhost:8080/"
        self.GAE_URL = "http://prototype.mol-lab.appspot.com/"        
        self.VALID_ID_SERVICE_URL = "%sapi/validkey" % self.GAE_URL
        self.LAYER_URL = "%slayers" % self.GAE_URL
        #self.TILE_URL = 'http://localhost:5002/api/tiles/animalia/species/%s/zoom/x/y.png'
        self.TILE_URL = 'layers/api/tiles/animalia/species/%s/zoom/x/y.png'
        self.NEW_RASTER_JOB_TYPE = 'newraster'
        self.NEW_SHP_JOB_TYPE = 'newshp'
        self.BULKLOAD_TILES_JOB_TYPE = 'bulkload-tiles'
        self.Q_ITEM_FULL_PATH = 'fullpath'
        self.Q_ITEM_JOB_TYPE = 'jobtype'
        self.TILE_QUEUE_THREADS = 1
        self.TILE_MAX_ZOOM = 6
        self.TILE_JOB_LIMIT = 2 #number of tiling threads
        self.QUEUED_LAYERS = {}
