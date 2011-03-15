// =============================================================================
// Map object

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
    this.layers = [];
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
            mol.util.log('Map handling event: ' + mol.event.Types.ADD_CUSTOM_MAP_CONTROL);
            self.addController(divId, position);
        }
    );
    mol.eventBus.bind(
        mol.event.Types.ADD_NEW_MAP_LAYER,
        function(layer, id) {
            mol.util.log('Map handling event: ' + mol.event.Types.ADD_NEW_MAP_LAYER);
            var tmp = self.layers.reverse;
            tmp.push({'id': id, 'layer': layer});
            self.layers = tmp.reverse;
        }
    );
    mol.eventBus.bind(
        mol.event.Types.REORDER_MAP_LAYERS,
        function(layerOrder) {
            mol.util.log('Map handling event: ' + mol.event.Types.REORDER_MAP_LAYERS);
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

// =============================================================================
// Layer object
    
/**
 * Constructor for the Layer object.
 * 
 * @param options An object that contains options for type, source, name, data
 * @constructor
 */
mol.maps.Layer = function(options) {  
    this.type = options.type;
    this.source = options.source;
    this.name = options.name;
    this.data = options.data;
    if (this.type) {        
        this.build();
        return;
    } 
    this.showTypesUi();
};

/**
 * Builds the layer by selecting an engine and source.
 */
mol.maps.Layer.prototype.build = function() {
    switch (this.type) {
    case "points":
        this.engine = new mol.engines.PointsEngine();
        if (!this.source) {
            //for the future when more soruces are available
            this.engine.source = 'gbif';
        } else {
            this.engine.source = this.source;
        }
        break;
    case "range":
        this.engine = new mol.engines.RangeEngine();
        if (!this.source){
            //for the future when more soruces are available
            this.engine.source = 'mol';
        } else {
            this.engine.source = this.source;
        }
        break;
    }
    mol.util.log('Layer built with engine for ' + this.type);
};

/**
 * Shows the types UI.
 */
mol.maps.Layer.prototype.showTypesUi = function() {
  var dialog = null,
      buttonPoints = null,
      buttonRange = null,
      self = this;
    dialog = $('<div class="dialog list" id="add_new_layer_dialog">');
    buttonPoints = $('<button>').attr(
        {"id":"add_points_button","class":"dialog_buttons"}).html('Add Points');
    $(dialog).append(buttonPoints);
    buttonRange = $('<button>').attr(
        {"id":"add_range_button","class":"dialog_buttons"}).html('Add Range Map');
    $(dialog).append(buttonRange);    
    $(buttonPoints).click(
        function() {
            mol.util.log('Layer.buttonPoints.click');
            self.type = 'points';
            self.build();
        }
    );
    $(buttonRange).click(
        function() {
            mol.util.log('Layer.buttonRange.click');
            self.type = 'range';
            self.build();
        }
    );        
    
    mol.util.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
    mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, dialog);                                         
};

