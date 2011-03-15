MOL = (function ( $ ) {  
    var self = this;
    var layer = {}; //layers has form layer[0] = {'id'=someide,'layer':Layer()} etc. that way we can use this to also reflect changes in the LayerStackUI
    //var bus = new EventBus();
    
    var Map = function( ) {
        var _self = this;
        //TODO: Event bus listener to call _self.addController for new controllers
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
            },
            addController: function(divId,position){   
                var overlayDiv = document.getElementById(divId);
                _self.map.controls[position].push(overlayDiv);
            }
        };
    };

    var LayerStackUI = function(){
        var _self = this;
            var container,layers,menu,list,position,addController;
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
                
                
                $('#layers #delete_layer').click(function(){
                    var id = $("#layers .layer.list input:checked");
                    //TODO: Send event bus a delete for this id
                });
                $('#layers #add_layer').click(function(){
                    //TODO: Send an event bus the Add call, which does a new Layer().init() and appends it to the MOL.layers array
                });
                
                //TODO: remove #tester and next line
                $('#tester').append(_self.container);
                
                //TODO: add Evenbus call that tells Map to add this new Controller via addController(divId,position)
            },
        };
    };

    var Layer = function(){
        var _self = this;
        var Engine, type, source, name, data;
        var setType = function(type){
            _self.type = type;
            switch ( type ) {
                case "points":
                    _self.Engine = new Engine().Points();
                    if (!_self.source){
                        //for the future when more soruces are available
                        _self.Engine.setSource('gbif');
                    } else {
                        self.Engine.setSource(_self.source);
                    }
                    break;
                case "range":
                    _self.Engine = new Engine().Range();
                    if (!_self.source){
                        //for the future when more soruces are available
                        _self.Engine.setSource('mol');
                    } else {
                        self.Engine.setSource(_self.source);
                    }
                    break;
            }
        }
        
        return {
            init: function(){
                /* populate base Layer stuff here */
                /* create a UI element to ask what type of layer it is with a direct lister */
                /* Register the UI element in the Event Bus so that the LayerStackUI sees it and appends it to the stack */
                if (!_self.type){
                    var dialog = $('<div class="dialog list" id="add_new_layer_dialog">');
                    var buttonPoints = $('<button>').attr({"id":"add_points_button","class":"dialog_buttons"}).html('Add Points')
                    $(dialog).append(buttonPoints)
                    
                    var buttonRange = $('<button>').attr({"id":"add_range_button","class":"dialog_buttons"}).html('Add Range Map')
                    $(dialog).append(buttonRange)
                    
                    $(buttonPoints).click(function(){
                        _self.setType('points');
                    });
                    $(buttonRange).click(function(){
                        _self.setType('range');
                    });
                } else {
                    _self.setType(_self.type);
                }
            },
        };
    };

    var Interface = function(context) {
        var _self = this;
        _self.mapdiv = $("#map");
        _self.rangemap = new Map();
        _self.rangemap.init(_self.mapdiv);
        
        _self.layerstackui = new LayerStackUI();
        _self.layerstackui.init(context);
        
    };
    
    var Engine = function(){
        return {
            Points: function(){
                //populate all methods of the Points engine
                _self = this;
                    var source, name;
                
                
                return {
                    setSource: function(source){
                        case "gbif":
                            _self.source = source;
                            if (!_self.name){
                                $(dialog).append($('<div id="add_points_dialog" class="dialog_button output">Get GBIF Points<input type="search" id="gbif_points_search_box"><a href="javascript:" id="gbif_points_search">Go</a></div>'));
                            }else{
                                _self.setName(_self.name);
                            }
                            break;
                        }
                    }
            },
            Range: function(){
                //populate all methods of the Range engine
                _self = this;
                    var source, name;
                return {
                    setSource: function(source){
                        case "mol":
                            _self.source = source;
                            if (!_self.name){
                                $(dialog).append($('<div id="add_range_dialog" class="dialog_button output">Get MOL Range Map<input type="search" id="mol_range_search_box"><a href="javascript:" id="mol_range_search">Go</a></div></div>'));
                            }else{
                                _self.setName(_self.name);
                            }
                            break;
                        }
                    }
            }
        }
    }
    return {
		// constructor
		Viz: function( context ){
            var _self = this;
            _self.context = context;
            var _interface = new Interface(context);
        },
        Widget: function(){
            /*build stuff different here */
        },
    };

})(jQuery);
