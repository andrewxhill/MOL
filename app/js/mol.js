MOL = (function ( $ ) {  
    var self = this;
    self.map = null;
    
    var Map = function( ) {
        var _self = this;
            var context,center,options,map;
            
        return {
            init: function( context ){
                console.log($(context).attr('id'));
                _self.context = context;
                _self.center = new google.maps.LatLng(0,0);            
                _self.options = {
                    zoom: 2,
                    maxZoom: 20,
                    center: _self.center,
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                };
                var layersDiv = document.getElementById($(context).attr('id'));
                _self.map = new google.maps.Map(layersDiv, _self.options);
            }
        }
    }
    var LayerStackUI = function(){
        return {
            init: function(context){
                /* create widget ui framework here */
            },
        }
    }
    var Layer = function(){
        var Engine = null;
        
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
        }
    }
    var Interface = function( context ) {
        var _self = this;
        _self.rangemap = $("<div>")
                            .attr({"id":"map"})
                            .css({"width":"800px",
                                  "height": "400px",
                                  "background-color":"black",
                                 });
        $(context).append("<div>hello header</div>");
        $(context).append(_self.rangemap);
        _self.map = new Map();
        _self.map.init(_self.rangemap);
        
        //self.layerstackui = new LayerStackUI();
        //self.layerstackui.init(self.rangemap);
        
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
    }
})(jQuery);
