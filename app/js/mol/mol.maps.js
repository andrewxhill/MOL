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
        this.mouse = {};
        $().mousedown(
            function(e){
                this.e.down=true;
            }
        );
        $().mouseup(
            function(e){
                this.e.down=false;
            }
        );
        return new mol.maps.Map();
    }
    var contextDoc = document.getElementById($(context).attr('id')),
        mapDiv = $("#map"), // This is a hack... couldn't get contextDoc working
        self = this;
    this.layers = [];
    this.context = context;
    this.options = {
        zoom: 2,
        maxZoom: 15,
        mapTypeControlOptions: {position: google.maps.ControlPosition.BOTTOM_LEFT},
        center: new google.maps.LatLng(0,0),
        mapTypeId: google.maps.MapTypeId.TERRAIN
    };
    this.map = new google.maps.Map(mapDiv[0], this.options);
    this.wireEvents();
    
    this.rightController = $('<div>').attr({'id': 'right-controller'});
    this.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(this.rightController[0]);
    
    this.infoController = $('<div>').attr({'id': 'info-controller'});
    this.map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(this.infoController[0]);
    $(this.infoController).disableSelection();
    
        
    $(this.rightController).mouseleave(function(){
        console.log('try');
        mol.eventBus.trigger(
            mol.event.Types.CONTROLLER_FOCUS_UPDATE,
            'controller', 
            false
        );   
    });
    
    function WidgetsTest() {
        var id = 'filter-widget-container';
        var dialog = $('<div>')
                        .attr({'id':id,'class':'widget-container'});
        var menu = $('<div>').attr({'id': 'menu'});
        var list = $('<div>').attr({'id': 'list'});
        var filters = $('<div>').attr({'id': 'filters'});
        var options = $('<ul>').attr({'class': 'options list'});
        var label = $('<li id="menuLabel" class="option list">Filters</li>');
        
        /*
        var year = $("<div>")
                        .attr({"id":"year", "class":"filter list"});
		var yeartitle = $("<div class='title'>Year min</div>");
		var yearslider = $("<input>")
                            .attr({"id":"yearslider","class":"slider","type":"range","min":"0","max":"100"});
        
        $(year).append(yeartitle);
        $(year).append(yearslider);
        $(filters).append(year);
        
        var cuim = $("<div>")
                        .attr({"id":"year", "class":"filter list"});
		var cuimtitle = $("<div class='title'>Max cuim</div>");
		var cuimslider = $("<input>")
                            .attr({"id":"yearslider","class":"slider","type":"range","min":"0","max":"100"});
        $(cuim).append(cuimtitle);
        $(cuim).append(cuimslider);
        $(filters).append(cuim);
        
        
        $(list).append(filters);
        */
        $(options).append(label);
        $(menu).append(options);
        $(dialog).append(menu);
        $(dialog).append(list);
        $(dialog).disableSelection();
        mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'right-controller');
        /* add this back
        mol.eventBus.trigger( mol.event.Types.CONTROLLER_FOCUS_UPDATE, 
            $(dialog).attr('id'), 
            true,false,true); 
        */
        
        
        id = 'tools-widget-container';
        dialog = $('<div>')
                        .attr({'id':id,'class':'widget-container'});
        menu = $('<div>').attr({'id': 'menu'});
        list = $('<div>').attr({'id': 'list'});
        filters = $('<div>').attr({'id': 'filters'});
        options = $('<ul>').attr({'class': 'options list'});
        label = $('<li id="menuLabel" class="option list">Tools</li>');
        $(options).append(label);
        $(menu).append(options);
        $(dialog).append(menu);
        $(dialog).append(list);
        $(dialog).disableSelection();
        mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'right-controller');
    }
    
    WidgetsTest();
    
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
            $(divId).find("#menuLabel").mouseover(function(){ 
                mol.eventBus.trigger(
                    mol.event.Types.CONTROLLER_FOCUS_UPDATE,
                    $(divId).attr('id'), 
                    true
                ); 
            });
            $("#right-controller").mouseleave(function(){
                console.log('try');
                mol.eventBus.trigger(
                    mol.event.Types.CONTROLLER_FOCUS_UPDATE,
                    $(divId).attr('id'), 
                    false
                );   
            });
            break;
        case 'info-controller':
            if ($(this.infoController).find("#"+divId[0].id).length==0){
                $(this.infoController).prepend(divId);
                setTimeout(function(){
                    $(divId).fadeOut('slow', function() {
                        $(divId).remove();
                    });
                },8000);
            }
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
    if (!(this instanceof mol.maps.Layer)) {
        return new mol.maps.Layer(options);
    }
    if (options) {      
        this.map = options.map,
        this.type = options.type;
        this.source = options.source;
        this.name = options.name;
        this.data = options.data;
    }
    if (this.type) {        
        this.build();
        return this;
    } 
    this.showTypesUi();
    return this;
};

/**
 * Builds the layer by selecting an engine and source.
 * 
 */
mol.maps.Layer.prototype.build = function() {
    switch (this.type) {
    case "points":
        this.engine = new mol.engines.PointsEngine({map: this.map});
        mol.log('Engine name ' + this.engine.getName());
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
            this.engine.setSource('MOL');
        } else {
            this.engine.setSource(this.source);
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
