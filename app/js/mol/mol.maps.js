// =============================================================================
// Map object

/**
 * The Map.
 * 
 * @constructor
 * @param context A div element
 * 
 */
mol.maps.Map = function(context) {
    if (!(this instanceof mol.maps.Map)) {
        return new mol.maps.Map();
    }
    var contextDoc = document.getElementById($(context).attr('id')),
        mapDiv = $("#map"), // This is a hack... couldn't get contextDoc working
        self = this;
    this.layers = [];
    this.context = context;
    this.options = {
        zoom: 2,
        maxZoom: 20,
        mapTypeControlOptions: {position: google.maps.ControlPosition.BOTTOM_LEFT},
        center: new google.maps.LatLng(0,0),
        mapTypeId: google.maps.MapTypeId.TERRAIN
    };
    this.map = new google.maps.Map(mapDiv[0], this.options);
    this.wireEvents();
    
    this.rightController = $('<div>').attr({'id': 'right-controller'});
    this.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(this.rightController[0]);
    
    function filterWidgetTest() {
        var dialog = $('<div>')
                        .attr({'id':'filter-widget-container','class':'widget-container'});
        var menu = $('<div>').attr({'id': 'menu'});
        var list = $('<div>').attr({'id': 'list'});
        var filters = $('<div>').attr({'id': 'filters'});
        var options = $('<ul>').attr({'class': 'options list'});
        var label = $('<li id="menuLabel" class="option list">Filters</li>');
        
        var year = $("<div>")
                        .attr({"id":"year", "class":"filter list"});
		var yeartitle = $("<div class='title'>Year min</div>")
		//var yearslider = $("<input>")
        //                    .attr({"id":"yearslider","class":"slider","type":"range","min":"0","max":"100"});
        var yearslider = $('<div id="yearslider" class="slider">');
        
        $(year).append(yeartitle);
        $(year).append(yearslider);
        $(filters).append(year);
        
        var cuim = $("<div>")
                        .attr({"id":"year", "class":"filter list"});
		var cuimtitle = $("<div class='title'>Max cuim</div>")
		var cuimslider = $("<input>")
                            .attr({"id":"yearslider","class":"slider","type":"range","min":"0","max":"100"});
        $(cuim).append(cuimtitle);
        $(cuim).append(cuimslider);
        $(filters).append(cuim);
        
        
        $(options).append(label);
        $(menu).append(options);
        $(list).append(filters);
        $(dialog).append(menu);
        $(dialog).append(list);
        mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'right-controller');
    }
    
    filterWidgetTest();
    
    return this;
};

/**
 * Wires event handlers to the EventBus for the Map.
 * 
 */
mol.maps.Map.prototype.wireEvents = function() {
    var self = this;
    
    mol.eventBus.bind(
        mol.event.Types.ADD_CUSTOM_MAP_CONTROL, 
        function(divId, position, first) {
            mol.log('Map handling event: ' + 
                         mol.event.Types.ADD_CUSTOM_MAP_CONTROL);
            self.addController(divId, position, first);
        }
    );
    mol.eventBus.bind(
        mol.event.Types.ADD_NEW_MAP_LAYER,
        function(layer, id) {
            mol.log('Map handling event: ' + 
                         mol.event.Types.ADD_NEW_MAP_LAYER);
            var tmp = self.layers.reverse;
            tmp.push({'id': id, 'layer': layer});
            self.layers = tmp.reverse;
        }
    );
    mol.eventBus.bind(
        mol.event.Types.REORDER_MAP_LAYERS,
        function(layerOrder) {
            mol.log('Map handling event: ' + 
                         mol.event.Types.REORDER_MAP_LAYERS);
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

/**
 * Adds a widget to the map at a given position.
 * 
 * @param divId The div of the widget to add
 * @param position The position on the map to place the widget
 * 
 */
mol.maps.Map.prototype.addController = function(divId, which, first) { 
    switch(which){
        case 'right-controller':
            if (first) {
                $(this.rightController).prepend(divId);
            } else {
                $(this.rightController).append(divId);
            }
            $(divId).mouseover(function(){
                //self.setStackFocus(true);    
                mol.eventBus.trigger(
                    mol.event.Types.CONTROLLER_FOCUS_UPDATE,
                    $(divId).attr('id'), 
                    true
                );      
            });
            $(divId).mouseleave(function(){
                //self.setStackFocus(false,true);  
                mol.eventBus.trigger(
                    mol.event.Types.CONTROLLER_FOCUS_UPDATE,
                    $(divId).attr('id'), 
                    false,
                    true
                );   
            });
            break;
    }
};


// =============================================================================
// Layer object
    
/**
 * Constructor for the Layer object.
 * 
 * @constructor
 * @param options An object that contains options for type, source, name, data
 * 
 */
mol.maps.Layer = function(options) {  
    if (options) {        
        this.type = options.type;
        this.source = options.source;
        this.name = options.name;
        this.data = options.data;
    }
    if (this.type) {        
        this.build();
        return;
    } 
    this.showTypesUi();
};

/**
 * Builds the layer by selecting an engine and source.
 * 
 */
mol.maps.Layer.prototype.build = function() {
    switch (this.type) {
    case "points":
        this.engine = new mol.engines.PointsEngine();
        if (!this.source) {
            //for the future when more soruces are available
            this.engine.setSource('GBIF');
        } else {
            this.engine.setSource(this.source);
        }
        break;
    case "range":
        this.engine = new mol.engines.RangeEngine();
        if (!this.source){
            //for the future when more soruces are available
            this.engine.source('MOL');
        } else {
            this.engine.source(this.source);
        }
        break;
    }
    mol.log('Layer built with engine for ' + this.type);
};

/**
 * Shows the types UI and wires UI event handlers and EventBus handlers.
 * 
 */
mol.maps.Layer.prototype.showTypesUi = function() {
  var dialog = null,
      buttonPoints = null,
      buttonRange = null,
      self = this;
    dialog = $('<li class="dialog list" id="add_new_layer_dialog">');
    buttonRange = $('<button>').attr(
        {"id":"add_range_button","class":"dialog_buttons"}).html('Add Range Map');
    $(dialog).append(buttonRange);   
    buttonPoints = $('<button>').attr(
        {"id":"add_points_button","class":"dialog_buttons"}).html('Add Points');
    $(dialog).append(buttonPoints); 
    $(buttonPoints).click(
        function() {       
            mol.log('Layer.buttonPoints.click');
            self.type = 'points';
            self.build();
        }
    );
    $(buttonRange).click(
        function() {
            mol.log('Layer.buttonRange.click');
            self.type = 'range';
            self.build();
        }
    );            
    mol.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
    mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, dialog);                                         
};
