var MOL = MOL || {};

MOL.init = function () {  

    /**
     * Event bus.
     */
    MOL.EventBus = function() {
        if (!(this instanceof MOL.EventBus)) {
            return new MOL.EventBus();
        }
        _.extend(this, Backbone.Events);
        return this;
    };
    
    
    var Map = function( ) {
        var _self = this;
        var layers = [];
        //TODO: Event bus listener to call _self.addController for new controllers

        _self.addController = function(divId,position){   
            //var overlayDiv = document.getElementById(divId);
            _self.map.controls[position].push(divId[0]);
        };
        
        return {
            init: function(context) {
                _self.context = context;
                _self.center = new google.maps.LatLng(0,0);            
                _self.options = {
                    zoom: 2,
                    maxZoom: 20,
                    center: _self.center,
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                };
                var contextDoc = document.getElementById($(context).attr('id'));
                _self.map = new google.maps.Map(contextDoc, _self.options);

                // Wires up an event handler for 'add-custom-map-controller' events:
                MOL.eventBus.bind('add-custom-map-controller', 
                                  function(divId, position) {
                                      _self.addController(divId, position);
                                  });
                MOL.eventBus.bind('add-new-map-layer', 
                                  function(layer,id) {
                                      var tmp = _self.layers.reverse;
                                      tmp.push({'id': id, 'layer': layer});
                                      _self.layers = tmp.reverse;
                                  });
                MOL.eventBus.bind('reorder-map-layers', 
                                  function(layerOrder) {
                                      //layerOrder is an ordered list of layerIds
                                      var tmp = new Array(_self.layers.length);
                                      var ct = 0;
                                      for (var i in layerOrder){
                                          tmp[ct] = layerOrder[i];
                                          ct++;
                                      }
                                      _self.layers = tmp;
                                  });
            }
        };
    };

    var LayerStackUI = function(){
        var _self = this;
            var id,container,layers,menu,list,position,addController;
            //TODO: add an event bus listener that will look for new Elements to be added to the (#layers #list)
        return {
            init: function(context){
                /* create widget ui framework here */
                var options = $('<ul>').attr({'class': 'options list'});
                $(options).append(
                    $('<li>').attr({'class':'option list','id':'add'})
                        .append($('<a>').attr({'id': 'add_layer', 'href':'javascript:'}).html('Add'))
                );
                $(options).append(
                    $('<li>').attr({'class':'option list','id':'delete'})
                        .append($('<a>').attr({'id': 'delete_layer', 'href':'javascript:'}).html('Delete'))
                );
                _self.menu = $('<div>').attr({'id':'menu'});
                $(_self.menu).append(options);
                
                _self.list = $('<div>').attr({'id':'list'});
                
                _self.layers = $('<div>').attr({'id':'layers'});
                $(_self.layers).append(_self.menu);
                $(_self.layers).append(_self.list);
                
                
                _self.container = $('<div>').attr({'id':'widget-container'});
                $(_self.container).append(_self.layers);
                
                _self.id = "widget-container";
                // Triggers 'add-custom-map-controller' event on the bus:
                MOL.eventBus.trigger('add-custom-map-controller', 
                                     _self.container, 
                                     google.maps.ControlPosition.TOP_RIGHT);
                                     
                $('#layers #delete_layer').click(function(){
                    console.log('delete');
                    var id = $("#layers .layer.list input:checked");
                    //TODO: Send event bus a delete for this id
                });
                $('#layers #add_layer').click(function(){
                    console.log('add');
                    var layer = new Layer();
                    layer.init();
                    //TODO: Send an event bus the Add call, which does a new Layer().init() and appends it to the MOL.layers array
                });
                
                
            }
        };
    };

    var Layer = function(){
        var _self = this;
        var Engine, type, source, name, data;
        var setType = function(type){
            _self.type = type;
            switch ( type ) {
                case "points":
                    _self.Engine = new Engines().Points();
                    if (!_self.source){
                        //for the future when more soruces are available
                        _self.Engine.setSource('gbif');
                    } else {
                        self.Engine.setSource(_self.source);
                    }
                    break;
                case "range":
                    _self.Engine = new Engines().Range();
                    if (!_self.source){
                        //for the future when more soruces are available
                        _self.Engine.setSource('mol');
                    } else {
                        self.Engine.setSource(_self.source);
                    }
                    break;
            }
        };
        
        return {
            init: function(){
                /* populate base Layer stuff here */
                /* create a UI element to ask what type of layer it is with a direct lister */
                /* Register the UI element in the Event Bus so that the LayerStackUI sees it and appends it to the stack */
                if (!_self.type){
                    var dialog = $('<div class="dialog list" id="add_new_layer_dialog">');
                    var buttonPoints = $('<button>').attr({"id":"add_points_button","class":"dialog_buttons"}).html('Add Points');
                    
                    $(dialog).append(buttonPoints);
                    
                    var buttonRange = $('<button>').attr({"id":"add_range_button","class":"dialog_buttons"}).html('Add Range Map');
                    $(dialog).append(buttonRange);
                    
                    $(buttonPoints).click(function(){
                        _self.setType('points');
                    });
                    $(buttonRange).click(function(){
                        _self.setType('range');
                    });
                    
                } else {
                    _self.setType(_self.type);
                }
            }
        };
    };
    
    var Engines = function(){
        return {
            Points: function(){
                //populate all methods of the Points engine
                var _self = this;
                var type='points';
                var source, name;
                return {
                    setSource: function(source){
                        switch ( source ) {
                            case "gbif":
                                _self.source = source;
                                if (!_self.name){
                                    var dialog = $("div");
                                    $(dialog).append($('<div id="add_points_dialog" class="dialog_button output">Get GBIF Points<input type="search" id="gbif_points_search_box"><a href="javascript:" id="gbif_points_search">Go</a></div>'));
                                }else{
                                    _self.setName(_self.name);
                                }
                                break;
                            }
                        }
                    };
            },
            Range: function(){
                //populate all methods of the Range engine
                var _self = this;
                var type='range';
                var source, name;
                return {
                    setSource: function(source){
                        switch ( source ) {
                            case "mol":
                                _self.source = source;
                                if (!_self.name){
                                    var dialog = $("div");
                                    $(dialog).append($('<div id="add_range_dialog" class="dialog_button output">Get MOL Range Map<input type="search" id="mol_range_search_box"><a href="javascript:" id="mol_range_search">Go</a></div></div>'));
                                }else{
                                    _self.setName(_self.name);
                                }
                                break;
                            }
                        }
                    };
            }
        };
    };
    
    MOL = {
		// constructor
		Viz: function( context ){
            var _self = this;
            _self.context = context;
            _self.mapdiv = $(context);
            _self.rangemap = new Map();
            _self.rangemap.init(_self.mapdiv);
            _self.layerstackui = new LayerStackUI();
            _self.layerstackui.init(context);
        },
        Widget: function(){
            /*build stuff different here */
        },
        eventBus: new MOL.EventBus()
    };

};
