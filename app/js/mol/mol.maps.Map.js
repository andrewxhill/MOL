/**
 * The Map.
 * 
 * @constructor
 */
mol.maps.Map = function(context) {
    if (!(this instanceof mol.maps.Map)) {
        return new mol.maps.Map();
    }
    var contextDoc = document.getElementById($(context).attr('id')),
        mapDiv = $("#map"),
        self = this;
    this.context = context;
    this.options = {
        zoom: 2,
        maxZoom: 20,
        center: new google.maps.LatLng(0,0),
        mapTypeId: google.maps.MapTypeId.TERRAIN
    };
    this.map = new google.maps.Map(mapDiv[0], this.options);
    this.wireEvents();
    return this;
};
    
mol.maps.Map.prototype.wireEvents = function() {
    var self = this;
    mol.eventBus.bind(
        mol.event.Types.ADD_CUSTOM_MAP_CONTROL, 
        function(divId, position) {
            self.addController(divId, position);
        }
    );
    mol.eventBus.bind(
        mol.event.Types.ADD_NEW_MAP_LAYER,
        function(layer, id) {
            var tmp = self.layers.reverse;
            tmp.push({'id': id, 'layer': layer});
            self.layers = tmp.reverse;
        }
    );
    mol.eventBus.bind(
        mol.event.Types.REORDER_MAP_LAYERS,
        function(layerOrder) {
            var tmp = new Array(self.layers.length),
                ct = 0;
            for (var i in layerOrder) {
                tmp[ct] = layerOrder[i];
                ct++;
            }
            self.layers = tmp;
        }
    );    
};

mol.maps.Map.prototype.addController = function(divId, position) {   
    this.map.controls[position].push(divId[0]);
};
    
