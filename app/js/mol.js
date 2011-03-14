MOL = (function ( $ ) {  
    self = this;
    self.map = null;
    
    var Map = function( ) {
        _self = this;
        return {
            init: function( context ){
                console.log($(context).attr('id'));
                
                var center = new google.maps.LatLng(0,0);            
                var Options = {
                    zoom: 2,
                    maxZoom: 20,
                    center: center,
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                };
                var layersDiv = document.getElementById($(context).attr('id'));
                var map = new google.maps.Map(layersDiv, Options);
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
        self.rangemap = $("<div>")
                            .attr({"id":"map"})
                            .css({"width":"300px",
                                  "height": "200px",
                                  "background-color":"black",
                                 });
        $(context).append("<div>hello header</div>");
        $(context).append(self.rangemap);
        self.map = new Map();
        self.map.init(self.rangemap);
        
        //self.layerstackui = new LayerStackUI();
        //self.layerstackui.init(self.rangemap);
        
    }
    
    return {
		// constructor
		Viz: function( context ){
            _self = this;
            _self.context = context;
            var _interface = new Interface(context);
        },
        Widget: function(){
            /*build stuff different here */
        },
    }
})(jQuery);
