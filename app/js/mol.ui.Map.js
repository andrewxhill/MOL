/**
 * Map module that wraps a Google Map and gives it the ability to handle app 
 * level events and perform AJAX calls to the server. It surfaces custom
 * map controls with predefined slots. 
 * 
 * Event binding:
 *     ADD_MAP_CONTROL - Adds a control to the map.
 *     ADD_LAYER - Displays the layer on the map.
 * 
 * Event triggering:
 *     None
 */
MOL.modules.Map = function(mol) { 
    
    mol.ui.Map = {};
    
    /**
     * The Map Engine.
     */
    mol.ui.Map.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constucts a new Map Engine.
             *
             * @param api the mol.ajax.Api for server communication
             * @param bus the mol.events.Bus for event handling 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;  
                this._points = {};
                this._layers = {};
                this._controlDivs = {};
            },            
            
            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                var MarkerCanvas = mol.ui.Map.MarkerCanvas;

                this._bindDisplay(new mol.ui.Map.Display(), container);

                this._markerCanvas = new MarkerCanvas(15, 15);

                this._addMapControlEventHandler();
                this._addLayerEventHandler();
                this._addColorEventHandler();
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('Map.Engine.go()');
            },

            _bindDisplay: function(display, container) {
                this._display = display;
                display.setEngine(this);                

                container.append(display.getElement());
                
                this._map = display.getMap();

                this._addControls();
            },

            _addControls: function() {
                var map = this._map,
                    controls = map.controls,
                    ControlPosition = google.maps.ControlPosition,
                    TOP_RIGHT = ControlPosition.TOP_RIGHT,
                    TOP_CENTER = ControlPosition.TOP_CENTER,
                    BOTTOM_LEFT = ControlPosition.BOTTOM_LEFT,
                    TOP_LEFT = ControlPosition.TOP_LEFT,
                    Control = mol.ui.Map.Control;
                
                this._rightControl = new Control('RightControl');
                controls[TOP_RIGHT].clear();
                controls[TOP_RIGHT].push(this._rightControl.getDiv());
                                
                this._centerTopControl = new Control('CenterTopControl');
                controls[TOP_CENTER].clear();
                controls[TOP_CENTER].push(this._centerTopControl.getDiv());

                this._leftTopControl = new Control('TopLeftControl');
                controls[TOP_LEFT].clear();
                controls[TOP_LEFT].push(this._leftTopControl.getDiv());  
                
                this._leftBottomControl = new Control('LeftBottomControl');
                controls[BOTTOM_LEFT].clear();
                controls[BOTTOM_LEFT].push(this._leftBottomControl.getDiv());                
            },

            /**
             * Adds an event handler for new layers.
             */
            _addLayerEventHandler: function() {
                var bus = this._bus,
                    LayerEvent = mol.events.LayerEvent,
                    ColorEvent = mol.events.ColorEvent,
                    deleteLayer = this._deleteLayer,
                    layers = this._layers,
                    self = this;
                
                bus.addHandler(
                    LayerEvent.TYPE,
                    function(event) {
                        var layer = event.getLayer(),
                            lid = layer.getId(),
                            action = event.getAction(),
                            config = {
                                action: 'get',
                                category: layer.getType(),
                                id: lid
                            };
                        
                        switch (action) {

                        case 'add':
                            layers[lid] = layer;
                            // We need a layer color before displaying it:
                            bus.fireEvent(new ColorEvent(config));
                            break;

                        case 'delete':
                            deleteLayer(lid);
                            break;

                        case 'checked':
                            mol.log.todo('Handle layer checked event');
                            self._toggleLayer(layers[lid], true);
                            break;
                            
                        case 'unchecked':
                            mol.log.todo('Handle layer unchecked event');
                            self._toggleLayer(layers[lid], false);
                            break;                            
                        }                        
                    }
                );
            },
            
            /**
             * Adds an event handler so that displays can be added to the map as
             * controls simply by firing a MapControlEvent.
             */
            _addMapControlEventHandler: function() {
                var bus = this._bus,
                    MapControlEvent = mol.events.MapControlEvent,
                    controls = this._map.controls,
                    controlDivs = this._controlDivs,
                    ControlPosition = mol.ui.Map.Control.ControlPosition,
                    TOP_RIGHT = ControlPosition.TOP_RIGHT,
                    TOP_CENTER = ControlPosition.TOP_CENTER,
                    BOTTOM_LEFT = ControlPosition.BOTTOM_LEFT,
                    TOP_LEFT = ControlPosition.TOP_LEFT,
                    topRightControl = this._rightControl,
                    leftTopControl = this._leftTopControl,
                    centerTopControl = this._centerTopControl,
                    leftBottomControl = this._leftBottomControl;
                                
                bus.addHandler(
                    MapControlEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            display = event.getDisplay(),
                            controlPosition = event.getControlPosition(),
                            displayPosition = event.getDisplayPosition(),
                            control = null;

                        switch (action) {

                        case 'add':
                            switch (controlPosition) {
                                
                            case TOP_RIGHT:
                                control = topRightControl;
                                break;
                                
                            case TOP_CENTER:
                                control = centerTopControl;
                                break;

                            case TOP_LEFT:
                                control = leftTopControl;
                                break;

                            case BOTTOM_LEFT:
                                control = leftBottomControl;
                                break;
                            }

                            control.addDisplay(display, displayPosition);

                        case 'remove':
                            // if (controlDivs[div]) {
                            //     controls.removeAt(controlDivs[div]);
                            //     delete controlDivs[div];
                            // }                           
                            
                        }
                    }
                );
            },

            _addColorEventHandler: function() {
                var ColorEvent = mol.events.ColorEvent,
                    bus = this._bus,
                    points = this._points,
                    layers = this._layers,
                    self = this,
                    map = this._map;
                
                bus.addHandler(
                    ColorEvent.TYPE,
                    function(event) {
                        var color = event.getColor(),
                            category = event.getCategory(),
                            layerId = event.getId(),
                            layer = layers[layerId],
                            action = event.getAction();

                        // Ignores event since we don't have the layer associated with it:
                        if (!layer) {
                            return;
                        }
                        
                        // Sets the layer color:
                        layer.setColor(color);

                        switch (action) {

                        case 'change':
                            switch (category) {
                                
                            case 'points':
                                // Gets the point icon based on color and either
                                // creates the points with new icons or updates 
                                // icons of existing points.
                                self._getPointIcon(
                                    color,
                                    function(icon) {
                                        layer.setIcon(icon);                                    
                                        if (!points[layerId]) {
                                            self._createPoints(layer);    
                                        } else {
                                            self._updateLayerColor(layer);
                                        }
                                    }
                                );
                                break;

                            case 'range':
                                map.overlayMapTypes.push(self._rangeImageMapType(layer, color));
                                break;                                
                            }                           
                        }
                    }
                );                
            },
            
            _updateLayer: function(layer) {
                _updateLayerColor(layer);
            },

            _updateLayerColor: function(layer) {
                var points = this._points[layer.getId()],
                    type = layer.getType(),
                    urls = this._getIconUrls(layer.getIcon()),
                    markerCanvas = this._markerCanvas,
                    iconUrl = urls.iconUrl,
                    w = markerCanvas.getIconWidth(),
                    h = markerCanvas.getIconHeight(),
                    point = null,
                    MarkerImage = google.maps.MarkerImage,
                    Size = google.maps.Size,
                    Marker = google.maps.Marker,
                    image = new MarkerImage(iconUrl, new Size(w, h));
                
                switch (type) {

                case 'points':
                    for (x in points) {
                        point = points[x];
                        if (point instanceof Marker) {
                            point.setIcon(image);
                        }                        
                    }
                    break;

                case 'range':
                    // TODO
                    break;

                }
            },

            _getPointIcon: function(color, callback) {
                var icon = new Image(),
                    src = '/api/colorimage/pm-color.png?'
                          + 'r=' + color.getRed() 
                          + '&g=' + color.getGreen() 
                          + '&b=' + color.getBlue();                
                icon.onload = function() {
                    callback(icon);
                };                
                icon.src = src;
            },

            /**
             * Deletes a layer from the map.
             * 
             * @param layerId the id of the layer to delete
             */
            _deleteLayer: function(layerId) {
                var points = this._points[layerId];
                for (x in points) {
                    points[x].setMap(null);
                    delete points[x];
                }
                delete this._points[layerId];
                this._points[layerId] = null;
            },

            /**
             * Displays the layer on the map.
             * 
             * @param the layer to display
             */
            _toggleLayer: function(layer, show) {
                var lid = layer.getId(),
                    type = layer.getType(),
                    points = this._points[lid],
                    map = show ? this._map : null;

                switch (type) {

                case 'points':
                    for (x in points) {
                        points[x].setMap(map);
                    }
                    
                case 'range':
                    // TODO
                    break;
                }
            },            

            _getIconUrls: function(icon) {
                var markerCanvas = this._markerCanvas,
                    canvasSupport = markerCanvas.canvasSupport(),
                    icons = markerCanvas.getIcons(),
                    background = icons.background,
                    foreground = icons.foreground,
                    error = icons.error,
                    ctx = markerCanvas.getContext(),
                    w = markerCanvas.getIconWidth(),
                    h = markerCanvas.getIconHeight(),
                    url = null,
                    errorUrl = null;
                if (!canvasSupport) {
                    return {iconUrl: icon.src, iconErrorUrl: icon.src};
                }
                ctx.drawImage(background, 0, 0, w, h);
                ctx.drawImage(icon, 0, 0, w, h);
                ctx.drawImage(foreground, 0, 0, w, h);
                url = markerCanvas.getDataURL();
                ctx.drawImage(error, 0, 0, w, h);
                errorUrl = markerCanvas.getDataURL();
                return {iconUrl: url, iconErrorUrl: errorUrl};
            },

            _createPoints: function(layer) {
                var lid = layer.getId(),
                    center = null,
                    marker = null,
                    circle = null,
                    coordinate = null,
                    resources = [],
                    occurrences = [],
                    data = layer._json,
                    icon = layer.getIcon(),
                    urls = this._getIconUrls(icon),
                    iconUrl = urls.iconUrl,
                    iconErrorUrl = urls.iconErrorUrl;
                this._points[lid] = [];
                for (p in data.records.publishers) {
                    resources = data.records.publishers[p].resources;
                    for (r in resources) {
                        occurrences = resources[r].occurrences;
                        for (o in occurrences) {
                            coordinate = occurrences[o].coordinates;
                            marker = this._createMarker(coordinate, iconUrl);
                            this._points[lid].push(marker);                      
                            circle = this._createCircle(
                                marker.getPosition(),
                                coordinate.coordinateUncertaintyInMeters);                            
                            if (circle) {
                                this._points[lid].push(circle);
                            }     
                        }
                    }
                }
            },

            /**
             * Private function that creates a Google circle object.
             * 
             * @param center the center LatLng of the circle
             * @param coordinateUncertaintyInMeters the circle radius
             * @return a new Google circle object
             */
            _createCircle: function(center, coordinateUncertaintyInMeters) {          
                if (coordinateUncertaintyInMeters == null) {
                    return null;
                }
                var map = this._display.getMap(),
                    radius = parseFloat(coordinateUncertaintyInMeters),
                    opacity = 0.85,
                    circle = new google.maps.Circle(
                        {
                            map: map,
                            center: center,
                            radius: radius,
                            fillColor: '#CEE3F6',
                            strokeWeight: 1,                                
                            zIndex: 5
                        }
                    );
                return circle;
            },
            
            /**
             * Private function that creates a Google marker object.
             * 
             * @param coordinate the coordinate longitude and latitude
             * @return a new Google marker object
             */
            _createMarker: function(coordinate, iconUrl) {
                var map = this._display.getMap(),
                    lat = parseFloat(coordinate.decimalLatitude),
                    lng = parseFloat(coordinate.decimalLongitude),
                    center = new google.maps.LatLng(lat, lng),
                    w = this._markerCanvas.getIconHeight(),
                    h = this._markerCanvas.getIconWidth(),
                    MarkerImage = google.maps.MarkerImage,
                    Size = google.maps.Size,
                    Marker = google.maps.Marker,
                    image = new MarkerImage(iconUrl, new Size(w, h)),
                    marker = new Marker(
                        { 
                            position: center,
                            map: map,
                            icon: image
                        }
                    );
                return marker;
            },

            _rangeImageMapType: function(layer, color) {   
                var self = this,
                    name = layer.getName().toLowerCase(),
                    speciesKey = 'animalia/species/' + name.replace(' ', '_'),
                    r = color.getRed(),
                    g = color.getGreen(),
                    b = color.getBlue();

                return new google.maps.ImageMapType(
                    {
                        name: speciesKey,

                        getTileUrl: function(coord, zoom) {
                            var normalizedCoord = self._getNormalizedCoord(coord, zoom);
                            if (!normalizedCoord) {
                                return null;
                            }
                            var bound = Math.pow(2, zoom);            
                            return "/layers/" + speciesKey + ".png?" +
                                "z=" + zoom + 
                                "&x=" + normalizedCoord.x + 
                                "&y=" + (normalizedCoord.y) +
                                "&r=" + r +
                                "&g=" + g +
                                "&b=" + b;
                                
                        },
                        tileSize: new google.maps.Size(256, 256),
                        isPng: true,
                        opacity: 0.5
                    });
            },

            /**
             * Returns normalized coordinates for a given map zoom level.
             * 
             * @param coord The coordinate
             * @param zoom The current zoom level
             */
            _getNormalizedCoord: function(coord, zoom) {
                var y = coord.y,
                    x = coord.x,
                    tileRange = 1 << zoom;
                // don't repeat across y-axis (vertically)
                if (y < 0 || y >= tileRange) {
                    return null;
                }
                // repeat across x-axis
                if (x < 0 || x >= tileRange) {
                    x = (x % tileRange + tileRange) % tileRange;
                }
                return {
                    x: x,
                    y: y
                };
            }
        }
    );

    /**
     * The top level placemark canvas container
     */
    mol.ui.Map.MarkerCanvas = mol.ui.Element.extend(
        {
            init: function(width, height) {
                var MarkerCanvas = mol.ui.Map.MarkerCanvas;
                
                this._canvasSupport = !!document.createElement('canvas').getContext;

                if (!this._canvasSupport) {
                    this._super();
                    return;
                }

                this._iconHeight = width;
                this._iconWidth = height;

                this._super('<canvas width=' + this._iconWidth + 
                            ' height=' + this._iconHeight + '>');

                this.setStyleName('mol-MarkerCanvas');

                this._ctx = this.getElement()[0].getContext("2d");

                this._iconLayers = {
                    background: new Image(),
                    foreground: new Image(),
                    error: new Image()
                };
                this._iconLayers.background.src = "/static/pm-background.png";
                this._iconLayers.foreground.src = "/static/pm-foreground.png";
                this._iconLayers.error.src = "/static/pm-error.png";
            },
            
            getIconWidth: function() {
                return this._iconWidth;
            },
            
            getIconHeight: function() {                
                return this._iconHeight;
            },

            getIcons: function() {
                return this._iconLayers;
            },
            
            canvasSupport: function() {
                return this._canvasSupport;
            },

            getContext: function() {
                return this._ctx;
            },

            getDataURL: function(){
                return this.getElement()[0].toDataURL("image/png");
            }
        }
    );
    

    mol.ui.Map.Control = mol.ui.Display.extend(
        {
            init: function(name) {
                var DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    TOP = DisplayPosition.TOP,
                    MIDDLE = DisplayPosition.MIDDLE,
                    BOTTOM = DisplayPosition.BOTTOM;

                this._super();
                this.disableSelection();
                
                this.setInnerHtml(this._html(name));

                this.setStyleName('mol-Map-' + name);

                this.findChild(TOP).setStyleName("TOP");
                this.findChild(MIDDLE).setStyleName("MIDDLE");
                this.findChild(BOTTOM).setStyleName("BOTTOM");
            },
                       
            getDiv: function() {
                return this.getElement()[0];                
            },
            
            /**
             * @param display - the mol.ui.Display to add
             * @param position - the mol.ui.Map.Control.DisplayPosition
             */
            addDisplay: function(display, position) {
                var DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    div = this.findChild(position);

                switch (position) {
                
                case DisplayPosition.FIRST:
                    this.prepend(display);
                    break;

                case DisplayPosition.LAST:
                    this.append(display);
                    break;

                default:            
                    div.append(display);
                }
            },

            _html: function(name) {
                return '<div id="' + name + '">' +
                       '    <div class="TOP"></div>' +
                       '    <div class="MIDDLE"></div>' +
                       '    <div class="BOTTOM"></div>' +
                       '</div>';
            }
        }
    );

    mol.ui.Map.Control.DisplayPosition = {
        FIRST: '.FIRST',
        TOP: '.TOP',
        MIDDLE: '.MIDDLE',
        BOTTOM: '.BOTTOM',
        LAST: '.LAST'
    };

    mol.ui.Map.Control.ControlPosition = {
        TOP_RIGHT: 'TOP_RIGHT',
        TOP_CENTER: 'TOP_CENTER',
        TOP_LEFT: 'TOP_LEFT',
        LEFT_BOTTOM: 'LEFT_BOTTOM'        
    };


    /**
     * The Map Display. It's basically a Google map attached to the 'map' div 
     * in the <body> element.
     */
    mol.ui.Map.Display = mol.ui.Display.extend(
        {

            /**
             * Constructs a new Map Display.
             * 
             * @param config the display configuration
             * @constructor
             */
            init: function(config) {
                var mapOptions = {
                    zoom: 2,
                    maxZoom: 15,
                    mapTypeControlOptions: {position: google.maps.ControlPosition.BOTTOM_LEFT},
                    center: new google.maps.LatLng(0,0),
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                };

                this._id = 'map';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
                this._map = new google.maps.Map($('#' + this._id)[0], mapOptions);
                /*
                var FT_TableID = 669006;
                var ECO_CODES = ["NT1404","NT0904"];
                for (e in ECO_CODES){
                    var ECO_CODE = ECO_CODES[e];
                    var FT_Query = "SELECT 'geometry' FROM "+FT_TableID+" WHERE 'eco_code' = '"+ECO_CODE+"';";
                    var FT_Options = { suppressInfoWindows: false, query: FT_Query };
                    var ft = new google.maps.FusionTablesLayer(FT_TableID, FT_Options);
                    ft.setMap(this._map);
                }*/
            },          
            
            
            /**
             * Returns the Google map object.
             */
            getMap: function() {
                return this._map;
            },

            /**
             * Returns the Google map controls array.
             */
            getMapControls: function() {
                return this._map.controls;
            }            
        }
    );
};
