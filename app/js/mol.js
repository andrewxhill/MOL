MOL = (function ( $ ) {  
    var mol = this;
    var map;
    var Map = function( ) {
        var _self = this;
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
                var layersDiv = document.getElementById($(context).attr('id'));
                MOL.map = new google.maps.Map(layersDiv, _self.options);
            },
        };
    };

    var LayerStackUI = function(){
        var _self = this;
            var layers,position,addController;
            
        _self.addController = function(div,position){   
                var overlayDiv = document.getElementById($(div).attr('id'));
                MOL.map.controls[position].push(overlayDiv);
            }
        return {
            init: function(context){
                /* create widget ui framework here */
                /*
                var options_list =  $('<li>').attr({'class':'option list','id':'add'})
                                        .append($('<a>').attr({'id': 'add_layer', 'href':'javascript:'}))
                var options = $('<ul>').attr({'class': 'options list'});
                $(options).append(options_list);
                
                var menu = $('div').attr({'id':'menu'});
                $(menu).append(options);
                */
                //var stack = $('div').attr({'id':'layers'});
                //layers.append(menu);
                _self.container = $('div')
                                    .attr({'id':'widget-container'})
                                    .css({'width':'50px','height':'50px','background-color':'red'});
                //$(container).append(stack);
                console.log(MOL);
                _self.position = google.maps.ControlPosition.RIGHT_TOP;
                _self.addController($(_self.container).attr('id'),_self.position);
            }
        };
    };

    var Layer = function(){
        var _self = this;
        var Engine, type;
        
        return {
            init: function(){
                /* populate base Layer stuff here */
                /* create a UI element to ask what type of layer it is with a direct lister */
                /* Register the UI element in the Event Bus so that the LayerStackUI sees it and appends it to the stack */
            },
            type: function(type){
                /* Layer type is set here from ui element */
                /* Pulls in one of the known engines for handling the type */
            }
        };
    };

    var Interface = function(context) {
        var _self = this;
        _self.rangemap = $("#map");
        _self.map = new Map();
        _self.map.init(_self.rangemap);
        
        self.layerstackui = new LayerStackUI();
        self.layerstackui.init(context);
        
    };
    
    return {
		// constructor
		Viz: function( context ){
            var _self = this;
            _self.context = context;
            var _interface = new Interface(context);
        },
        Widget: function(){
            /*build stuff different here */
        }
    };

})(jQuery);
