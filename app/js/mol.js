/**
 * This is the global MOL constructor for creating a sandbox environment composed
 * of modules. Everything that happens within this constructor is protected from
 * leaking into the global scope.
 * 
 */
function MOL() {
    var args = Array.prototype.slice.call(arguments),
        callback = args.pop(),
        modules = (args[0] && typeof args[0] === "string") ? args : args[0],
        i;
    if (!(this instanceof MOL)) {
        return new MOL(modules, callback);
    }
    if (!modules || modules === '*') {
        modules = [];
        for (i in MOL.modules) {
            if (MOL.modules.hasOwnProperty(i)) {
                modules.push(i);
            }
        }
    }
    for (i = 0; i < modules.length; i += 1) {
        MOL.modules[modules[i]](this);
    }
    callback(this);
    return this;
};

MOL.modules = {};

/**
 * Logging module that writes log messages to the console and to the Speed 
 * Tracer API. It contains convenience methods for info(), warn(), error(),
 * and todo().
 * 
 */
MOL.modules.log = function(mol) {    
    mol.log = {};

    mol.log.info = function(msg) {
        mol.log._write('INFO: ' + msg);
    };

    mol.log.warn = function(msg) {
        mol.log._write('WARN: ' + msg);
    };

    mol.log.error = function(msg) {
        mol.log._write('ERROR: ' + msg);
    };

    mol.log.todo = function(msg) {
        mol.log._write('TODO: '+ msg);
    };

    mol.log._write = function(msg) {
        var logger = window.console;
        if (mol.log.enabled) {
            if (logger && logger.markTimeline) {
                logger.markTimeline(msg);
            }
            console.log(msg);
        }
    };
};

/**
 * AJAX module for communicating with the server. Contains an Api object that 
 * can be used to execute requests paired with success and failure callbacks.
 */
MOL.modules.ajax = function(mol) {
    mol.ajax = {};

    mol.ajax.Api = Class.extend(
        {
            init: function(bus) {
                this._bus = bus;
            },

            execute: function(request, success, failure) {
                var xhr = null,
                    self = this;
                mol.log.info('Api handling request: ' + request.action);
                switch (request.action) {
                case 'load-layer':
                    this._loadLayer(request, success, failure);
                    return;
                case 'search':
                    xhr = $.post('/api/taxonomy', request.params, 'json');
                    break;                    
                case 'rangemap-metadata':
                    xhr = $.post('/api/tile/metadata/'+ request.params.speciesKey);
                    break;                    
                case 'gbif-points':
                    xhr = $.post('/api/points/gbif/'+ request.params.speciesKey);
                }
                if (xhr) {
                    xhr.success(success);
                    xhr.error(failure);
                } else {
                    failure('Bad request', request);
                }
            },
            
            _loadLayer: function(request, success, failure) {
                var layer = request.layer,
                    name = layer.getName().toLowerCase(),
                    type = layer.getType().toLowerCase(),
                    source = layer.getSource().toLowerCase(),
                    speciesKey = 'animalia/species/' + name.replace(' ', '_'),
                    xhr = null,
                    self = this;
                mol.log.info('Api sending AJAX request for layer ' + layer.getId());
                switch (type) {
                case 'points':
                    switch (source) {
                    case 'gbif':

                        xhr = $.post('/api/points/gbif/'+ speciesKey);                        
                        xhr.success(
                            function(json) {
                                mol.log.info('Api received AJAX response for layer ' 
                                             + layer.getId() + ' - trigger(NEW_LAYER)');
                                success(json);
                                self._bus.trigger(
                                    mol.events.NEW_LAYER,
                                    new mol.model.Layer(type, source, name, json)
                                );
                            }
                        );
                        xhr.error(failure);
                        break;
                    case 'vertnet':
                        break;
                    }
                    break;
                case 'range':
                    break;
                }                
                return null;
            }
        }
    );    
};

/**
 * Events module for working with application events. Contains a Bus object that
 * is used to bind event handlers and to trigger events.
 */
MOL.modules.events = function(mol) {
    mol.events = {};

    // Event types:
    mol.events.ADD_MAP_CONTROL = 'add_map_control';
    mol.events.ADD_LAYER_CLICK = 'add_layer_click';
    mol.events.DELETE_LAYER_CLICK = 'delete_layer_click';
    mol.events.NEW_LAYER = 'new_layer';
    mol.events.DELETE_LAYER = 'delete_layer';
    mol.events.SET_LAYER_COLOR = 'set_layer_color';
    mol.events.GET_NEXT_COLOR = 'get_next_color';
    mol.events.NEXT_COLOR = 'next_color';
    
    /**
     * The event bus.
     */
    mol.events.Bus = function() {
        if (!(this instanceof mol.events.Bus)) {
            return new mol.events.Bus();
        }
        _.extend(this, Backbone.Events);
        return this;
    };
};

/**
 * Exceptions module for handling exceptions.
 */
MOL.modules.exceptions = function(mol) {
    mol.exceptions = {};
    mol.exceptions.NotImplementedError = 'NotImplementedError';
    mol.exceptions.IllegalArgumentException = 'IllegalArgumentException';
};

/**
 * App module for running the app with a given configuration.
 */
MOL.modules.app = function(mol) {

    mol.app = {};

    mol.app.Instance = Class.extend(
        {
            init: function(config) {
                mol.log.enabled = config.logging;
                this._control = new mol.location.Control(config);
                Backbone.history.start();
            },

            run: function() {
                mol.log.info('App is now running!');
            }
        }
    );
};

/**
 * Location module for handling browser history and routing. Contains a Control
 * object used to initialize and start application ui modules and dispatch 
 * browser location changes.
 */
MOL.modules.location = function(mol) {
    mol.location = {};

    mol.location.Control = Backbone.Controller.extend(
        {
            initialize: function(config) {
                this._bus = config.bus || new mol.events.Bus();
                this._api = config.api || new mol.ajax.Api(this._bus);
                this._colorSetter = new mol.core.ColorSetter.Api({bus: this._bus});
                this._container = $('body');
                this._mapEngine = new mol.ui.Map.Engine(this._api, this._bus);
                this._mapEngine.start(this._container);
                this._layerControlEngine = new mol.ui.LayerControl.Engine(this._api, this._bus);
                this._layerControlEngine.start(this._container);                
            },
            
            routes: {
                ":sandbox/map": "map"
            },
            
            map: function(query) {
                this._mapEngine.go('place');
                this._layerControlEngine.go('place');
            }
        }
    );
};


/**
 * Model module.
 */
MOL.modules.model = function(mol) {
  
    mol.model = {};

    /**
     * The layer model.
     */
    mol.model.Layer = Class.extend(
        {
            init: function(type, source, name, json) {
                this._type = type;
                this._source = source;
                this._name = name;
                this._json = json;
                this._color = null;
                this._buildId();
            },
            
            getType: function() {
                return this._type;                
            },

            getSource: function() {
                return this._source;
            },
            
            getName: function() {
                return this._name;                
            },
            
            getId: function() {
                return this._id;                
            },
            
            getColor: function() {
                return this._color;                
            },
            
            setColor: function(color) {
                this._color = color;
            },
                             
            _buildId: function() {
                var type = this._type,
                    source = this._source,
                    name = this._name;
                if (this._id) {
                    return this._id;                    
                }
                this._id = [type, source, name.split(' ').join('_')].join('_');
                return this._id;
            }
        }
    );
};

/**
 * Module for core libraries.
 */
MOL.modules.core = function(mol) {
    mol.core = {};
};

/**
 * TODO: Andrew
 */
MOL.modules.ColorSetter = function(mol) {
    
    mol.core.ColorSetter = {};
    
    mol.core.ColorSetter.Color = Class.extend(
        {
            init: function(r, g, b) {
                this._r = r;
                this._g = g;
                this._b = b;
            },

            getRed: function() {
                return this._r;
            },
            
            getGreen: function() {
                return this._g;                
            },

            getBlue: function() {
                return this._b;
            },

            toString: function() {
                return 'Red=' + this._r + ', Green=' + this._g +', Blue=' + this._b;                    
            }
        }
    );

    mol.core.ColorSetter.Api = Class.extend(
        {
            /**
             * @constructor
             */
            init: function(config) {
                this._bus = config.bus;
                this._types = {};
                var self = this;
                this._bus.bind(
                    mol.events.GET_NEXT_COLOR,
                    function(type, id) {
                        mol.log.info('ColorSetter.Api.handle(GET_NEXT_COLOR) for ' + id);
                        var color = new mol.core.ColorSetter.Color(1, 2, 3);
                        mol.log.info('ColorSetter.Api.trigger(NEXT_COLOR) for ' + color.toString());
                        self._bus.trigger(
                            mol.events.NEXT_COLOR,
                            color,
                            type,
                            id
                        );
                    }
                    
                );
            }
        }
    );
};

/**
 * UI module.
 */
MOL.modules.ui = function(mol) {
    
    mol.ui = {};
    
    /**
     * Interface for UI Engine classes.
     */
    mol.ui.Engine = Class.extend(
        {
            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             */
            start: function(container) {
                throw mol.exceptions.NotImplementedError;
            },
            
            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             */
            go: function(place) {
                throw mol.exceptions.NotImplementedError;
            }
        }
    );

    /**
     * Base class for DOM elements.
     */
    mol.ui.Element = Class.extend(
        {
            /**
             * Constructs a new Element from an element.
             */
            init: function(element) {
                this._element = $(element);
            },
            
            /**
             * Returns the underlying DOM element object.
             */
            getElement: function() {
                return this._element;
            },
            
            /**
             * Proxy to JQuery.remove()
             */
            remove: function() {
                this._element.remove();
            },

            /**
             * Proxy to JQuery.click()
             */
            click: function(handler) {
                this._element.click(handler);
            },

            /**
             * Proxy to JQuery.append()
             */
            append: function(widget) {
                this._element.append(widget.getElement());
            },

            /**
             * Proxy to JQuery.prepend().
             */
            prepend: function(widget) {
                this._element.prepend(widget.getElement());
            },

            /**
             * Gets primary style name.
             */
            getStylePrimaryName: function() {
                var fullClassName = this.getStyleName(),
                    spaceIdx = fullClassName.indexOf(' ');
                if (spaceIdx >= 0) {
                    return fullClassName.substring(0, spaceIdx);
                }
                return fullClassName;
            },
            
            /**
             * Adds a secondary or dependent style name to this object.
             */
            addStyleName: function(style) {
                this._setStyleName(style, true);
            },
          
            /**
             * Adds a dependent style name by specifying the style name's suffix.
             */
            addStyleDependentName: function(styleSuffix) {
                this.addStyleName(this.getStylePrimaryName() + '-' + styleSuffix);
            },         

            /**
             * Gets all of the object's style names, as a space-separated list.
             */
            getStyleName: function() {
                var classAttr = this.getElement().attr('class');
                if (!classAttr) {
                    return '';                    
                }
                return classAttr.split(/\s+/).join(' ');
            },
          
            /**
             * Clears all of the object's style names and sets it to the given 
             * style.
             */
            setStyleName: function(style) {
                var s = style.split(/\s+/).join(' ');
                this.getElement().attr('class', s);
            },

            /**
             * Removes a dependent style name by specifying the style name's 
             * suffix.
             */
            removeStyleDependentName: function(style) {
                 this.removeStyleName(this.getPrimaryStyleName() + '-' + style);
            },          

            /**
             * Removes a style.
             */
            removeStyleName: function(style) {
                this._setStyleName(style, false);
            },

            /**
             * Sets the object's primary style name and updates all dependent 
             * style names.
             */
            setStylePrimaryName: function(style) {
                style = $.trim(style);
                if (style.length == 0) {
                    throw mol.exceptions.IllegalArgumentException;
                }
                this._updatePrimaryAndDependentStyleNames(style);
            },

            _setStyleName: function(style, add) {
                var oldStyle, idx, last, lastPos, begin, end, newClassName;
                style = $.trim(style);
                if (style.length == 0) {
                    throw mol.exceptions.IllegalArgumentException;
                }

                // Get the current style string.
                oldStyle = this.getStyleName();
                idx = oldStyle.indexOf(style);

                // Calculate matching index.
                while (idx != -1) {
                    if (idx == 0 || oldStyle.charAt(idx - 1) == ' ') {
                        last = idx + style.length;
                        lastPos = oldStyle.length;
                        if ((last == lastPos)
                            || ((last < lastPos) && (oldStyle.charAt(last) == ' '))) {
                            break;
                        }
                    }
                    idx = oldStyle.indexOf(style, idx + 1);
                }

                if (add) {
                    // Only add the style if it's not already present.
                    if (idx == -1) {
                        if (oldStyle.length > 0) {
                            oldStyle += " ";
                        }
                        this.setStyleName(oldStyle + style);
                    }
                } else {
                    // Don't try to remove the style if it's not there.
                    if (idx != -1) {
                        // Get the leading and trailing parts, without the removed name.
                        begin = $.trim(oldStyle.substring(0, idx));
                        end = $.trim(oldStyle.substring(idx + style.length));

                        // Some contortions to make sure we don't leave extra spaces.
                        if (begin.length == 0) {
                            newClassName = end;
                        } else if (end.length == 0) {
                            newClassName = begin;
                        } else {
                            newClassName = begin + " " + end;
                        }
                        this.setStyleName(newClassName);
                    }
                }
            },

             /**
              * Replaces all instances of the primary style name.
              */
            _updatePrimaryAndDependentStyleNames: function(newPrimaryStyle) {
                var classes = this.getStyleName().split(/\s+/);
                if (!classes) {
                    return;
                }                
                var oldPrimaryStyle = classes[0];
                var oldPrimaryStyleLen = oldPrimaryStyle.length;
                var name;                
                classes[0] = newPrimaryStyle;
                for (var i = 1, n = classes.length; i < n; i++) {
                    name = classes[i];
                    if (name.length > oldPrimaryStyleLen
                        && name.charAt(oldPrimaryStyleLen) == '-'
                        && name.indexOf(oldPrimaryStyle) == 0) {
                        classes[i] = newPrimaryStyle + name.substring(oldPrimaryStyleLen);
                    }
                }
                this.setStyleName(classes.join(" "));
            }
        }
    );

    /**
     * Base class for Displays.
     */
    mol.ui.Display = mol.ui.Element.extend(
        {
            /**
             * Constructs a new Display with the given DOM element.
             */
            init: function(element) {
                this._super(element);
            },
            
            /**
             * Sets the engine for this display.
             * 
             * @param engine a mol.ui.Engine subclass
             */
            setEngine: function(engine) {
                this._engine = engine;
            }
        }
    );
};

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
                this._overlays = {};
                this._layers = {};
                this._bindEvents();
                this._canvasSupport = false;
                if ( !!document.createElement('canvas').getContext ) {
                    this._iconHeight = 120;
                    this._iconWidth = 120;
                    this._canvasSupport = true;
                    this._markerCanvas = new mol.ui.Map.MarkerCanvas(this._iconWidth,this._iconHeight);
                    this._markerContext = this._markerCanvas.getContext();
                    this._iconLayers = {
                        background: new Image(),
                        foreground: new Image(),
                        error: new Image(),
                    }
                    this._iconLayers.background.src = "/static/pm-background.png";
                    this._iconLayers.foreground.src = "/static/pm-foreground.png";
                    this._iconLayers.error.src = "/static/pm-error.png";
                }
            },            
            
            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                var display = new mol.ui.Map.Display();
                display.setEngine(this);
                container.append(display.getElement());
                this._display = display;
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

            /**
             * Private function for binding event handles.
             */
            _bindEvents: function() {
                var self = this;
                // Adds a control to the map:
                this._bus.bind(
                    mol.events.ADD_MAP_CONTROL,
                    function(control, type) {
                        mol.log.info('Map.Engine.handle(ADD_MAP_CONTROL)');
                        var rc = self._display.getRightController();
                        switch (type) {
                        case mol.ui.Map.Display.ControlType.LAYER:
                            mol.log.info('Map.Engine adding layer control to map');
                            rc.addWidget('LayerControl', control);
                            break;
                        }
                    }
                ); 

                self._bus.bind(
                    mol.events.NEXT_COLOR,
                    function(color, type, id) {
                        mol.log.info('Map.Engine.handle(NEXT_COLOR)');
                        var layer = self._layers[id];
                        if (type === 'points' && layer && (id === layer.getId())) {
                            layer.setColor(color);
                            self._getMarkerIconUrl(
                                color, 
                                function(iconUrl, iconErrorUrl) {
                                    self._displayLayer(layer);
                                }
                            );
                            delete self._layers[id];
                            // TODO: trigger LAYER_CHANGE event
                        }
                    }
                );

                // Displays a new layer on the map:
                this._bus.bind(
                    mol.events.NEW_LAYER,
                    function(layer) {
                        mol.log.info('Map.Engine.handle(NEW_LAYER)');
                        self._layers[layer.getId()] = layer;
                        mol.log.info('Map.Engine.trigger(GET_NEXT_COLOR)');
                        self._bus.trigger(
                            mol.events.GET_NEXT_COLOR,
                            'points',
                            layer.getId()
                        );
                    }
                );
                
                // Deletes an existing layer from the map.
                this._bus.bind(
                    mol.events.DELETE_LAYER,
                    function(layerId) {
                        self._deleteLayer(layerId);
                    }
                );
            },

            /**
             * Sets the layer color.
             * 
             * @param layerId the id of the layer to color
             * @param color the mol.core.ColorSetter.Color object
             */
            _setLayerColor: function(layerId, color) {
                var overlays = this._overlays[layerId],
                    api = null;
                if (!overlays) {
                    return;
                }
                mol.log.info('Coloring layer ' + layerId + ': ' + color.toString());
                api = new mol.core.ColorSetter.Api();
                // TODO: Andrew
            },

            /**
             * Deletes a layer from the map.
             * 
             * @param layerId the id of the layer to delete
             */
            _deleteLayer: function(layerId) {
                var overlays = this._overlays[layerId];
                for (x in overlays) {
                    overlays[x].setMap(null);
                    delete overlays[x];
                }
                delete this._overlays[layerId];
                this._overlays[layerId] = null;
            },

            /**
             * Displays the layer on the map.
             * 
             * @param the layer to display
             */
            _displayLayer: function(layer) {
                var lid = layer.getId(),
                    type = layer.getType();
                if (this._overlays[lid]) {
                    // Duplicate layer.
                    return;
                } 
                mol.log.info('Map.Engine displaying new layer: ' + lid);
                switch (type) {
                case 'points':
                    this._displayPoints(layer);
                    break;
                case 'range':
                    this._displayRange(layer);
                    break;
                }
            },
            
            /**
             * Private function that displays a points layer on the map.
             * 
             * @param layer the points layer to display
             */
            _displayPoints: function(layer) {
                var lid = layer.getId(),
                    center = null,
                    marker = null,
                    circle = null,
                    coordinate = null,
                    resources = [],
                    occurrences = [],
                    data = layer._json,
                    icon = new Image(),
                    iconUrl = null,
                    iconErrorUrl = null;
                /*
                 * add method to set icon source here, using color
                 */
                if (_canvasSupport){
                    this._markerContext.drawImage(this._iconLayers.background, 0, 0, this._iconWidth, this._iconHeight);
                    this._markerContext.drawImage(icon, 0, 0, this._iconWidth, this._iconHeight);
                    this._markerContext.drawImage(this._iconLayers.foreground, 0, 0, this._iconWidth, this._iconHeight);
                    iconUrl = this._markerCanvas.getDataURL();
                    this._markerContext.drawImage(this._iconLayers.error, 0, 0, this._iconWidth, this._iconHeight);
                    iconErrorUrl = this._markerCanvas.getDataURL();
                } else {
                    iconUrl = icon.src;
                    iconErrorUrl = icon.src;
                }
                
                mol.log.info('Displaying points in color ' + layer.getColor().toString());
                
                this._overlays[lid] = [];
                for (p in data.records.providers) {
                    resources = data.records.providers[p].resources;
                    for (r in resources) {
                        occurrences = resources[r].occurrences;
                        for (o in occurrences) {
                            coordinate = occurrences[o].coordinates;
                            marker = this._createMarker(coordinate);
                            this._overlays[lid].push(marker);                      
                            circle = this._createCircle(
                                marker.getPosition(),
                                coordinate.coordinateUncertaintyInMeters);                            
                            if (circle) {
                                this._overlays[lid].push(circle);
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
            _createMarker: function(coordinate) {
                var map = this._display.getMap(),
                    lat = parseFloat(coordinate.decimalLatitude),
                    lng = parseFloat(coordinate.decimalLongitude),
                    center = new google.maps.LatLng(lat, lng),
                    marker = new google.maps.Marker(
                        { 
                            position: center,
                            map: map,
                            icon: 'http://labs.google.com/ridefinder/images/mm_20_red.png'
                        }
                    );
                return marker;
            }
        }
    );

    /**
     * The top level map control container. It gets added to the Google map as a
     * control. 
     */
    mol.ui.Map.RightController = mol.ui.Element.extend(
        {
            init: function() {
                this._super('<div>');
                this.setStyleName('mol-RightController');
                this._widgets = {};
            },

            addWidget: function(name, widget) {
                var wc = new mol.ui.Map.WidgetContainer(name);
                wc.setWidget(widget);
                this._widgets[name] = wc;
                this.getElement().append(wc.getElement());
            }
        }
    );

    /**
     * The container for Layers, Filters, Tools, and other control widgets on
     * the map. Its parent is RightController.
     */
    mol.ui.Map.WidgetContainer = mol.ui.Element.extend(
        {
            init: function(name) {
                this._super('<div>');
                this.setStyleName('mol-WidgetContainer');
                this._name = name;
            },

            setWidget: function(widget) {
                this.getElement().append(widget.getElement());
            }
        }        
    ),

    /**
     * The top level placemark canvas container
     */
    mol.ui.Map.MarkerCanvas = mol.ui.Element.extend(
        {
            init: function(width,height) {
                this._super('<canvas width='+width+' height='+height+'>');
                this.setStyleName('mol-MarkerCanvas');
                this._ctx = this.getElement()[0].getContext("2d");
                /**
                this._iconBackground.src = "/static/pm-background.png";
                this._iconForeground.src = "/static/pm-foreground.png";
                this._iconError.src = "/static/pm-error.png";
                this._icon = null;
                */
            },
            getContext: function(){
                return this._ctx;
            },
            getDataURL(){
                return this.getElement()[0].toDataURL("image/png");
            }
        }
    );
    
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
                },
                    position = google.maps.ControlPosition.TOP_RIGHT;
                this._id = 'map';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
                this._map = new google.maps.Map($('#' + this._id)[0], mapOptions);
                this._rightControl = new mol.ui.Map.RightController();
                this._map.controls[position].push(this._rightControl.getElement()[0]);
                mol.ui.Map.Display.ControlType = {
                    LAYERS: '#layers'
                };
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
            },
            
            /**
             * Returns the right controller.
             */
            getRightController: function() {
                return this._rightControl;
            }
        }
    );
};


/**
 * LayerControl module that presents a map control for adding or deleting layers. 
 * It can handle app level events and perform AJAX calls to the server.
 * 
 * Event binding:
 *     None
 * 
 * Event triggering:
 *     ADD_LAYER - Triggered when the Add widget is clicked
 *     DELETE_LAYER - Triggered when the Delete widget is clicked
 */
MOL.modules.LayerControl = function(mol) {

    mol.ui.LayerControl = {};

    /**
     * The LayerControl Engine.
     */
    mol.ui.LayerControl.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs a new engine.
             * 
             * @param api the mol.ajax.Api for server communication
             * @param bus the mol.events.Bus for event handling 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
            },

            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                var config = this._displayConfig(),
                    display = new mol.ui.LayerControl.Display(config),
                    position = google.maps.ControlPosition.TOP_RIGHT,
                    bus = this._bus;
                this._bindDisplay(display);
                // Triggers the ADD_MAP_CONTROL event which causes the display
                // to get added to the map as a control:
                mol.log.info('LayerControl.Engine.trigger(ADD_MAP_CONTROL)');
                bus.trigger(
                    mol.events.ADD_MAP_CONTROL,                     
                    display, 
                    mol.ui.Map.Display.ControlType.LAYER);
            },
            
            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('LayerControl.Engine.go()');
            },
            
            /**
             * Private function that binds the display by setting up click
             * handlers for the 'Add' and 'Delete' buttons.
             * 
             * @param display the mol.ui.LayerControl.Display object to bind 
             */
            _bindDisplay: function(display) {
                var self = this;
                this._display = display;
                display.setEngine(this);                
                // Adds click handler that triggers an ADD_LAYER_CLICK event:
                display.getAddLink().click(
                    function(event) {
                        mol.log.info('LayerControl.Display.AddLink.click()');
                        self._bus.trigger(mol.events.ADD_LAYER_CLICK);
                    }
                );
                // Adds click handler that triggers a DELETE_LAYER_CLICK event:
                display.getDeleteLink().click(
                    function(event) {
                        mol.log.info('LayerControl.Display.DeleteLink.click()');
                        self._bus.trigger(mol.events.DELETE_LAYER_CLICK);
                    }
                );
            },

            /**
             * Private function that returns a configuration object for the 
             * mol.ui.LayerControl.Display object.
             */
            _displayConfig: function() {
                return {
                    text: {
                        addLayer: 'Add',
                        deleteLayer: 'Delete',
                        layers: 'Layers'
                    }
                };
            }
        }
    );

    /**
     * The list menu that contains options for adding and deleting layers.
     */
    mol.ui.LayerControl.Menu = mol.ui.Element.extend(
        {
            init: function(name) {
                this._super('<ul>');
                this.setStylePrimaryName('mol-LayerControl-Menu');
                this._name = name;
                this._options = {};
                var label = new mol.ui.LayerControl.MenuOptionLabel(name);
                this._options[name] = label;
                this.append(label);
            },

            buildOptions: function(names) {
                var name = null,
                    option = null;
                for (x in names) {
                    name = names[x];
                    option = new mol.ui.LayerControl.MenuOption(name);
                    this._options[name] = option;
                    this.append(option);
                }
            },

            getOption: function(name) {
                return this._options[name];
            }
        }
    );

    /**
     * The menu option.
     */
    mol.ui.LayerControl.MenuOption = mol.ui.Element.extend(
        {
            init: function(name) {                
                this._super('<li>');
                this.setStyleName('mol-LayerControl-MenuOption');   
                this.addStyleName('mol-LayerControl-Menu');   
                this._link = new mol.ui.LayerControl.MenuOptionLink(name);
                this.getElement().append(this._link.getElement());
            },

            getLink: function() {
                return this._link;
            }
        }
    );
    
    /**
     * The menu option link.
     */
    mol.ui.LayerControl.MenuOptionLink = mol.ui.Element.extend(
        {
            init: function(name) {
                this._super('<a>');
                this.setStyleName('mol-LayerControl-MenuOptionLink');
                this.getElement().html(name);                
            }
        }
    );
    
    /**
     * The menu option label.
     */
    mol.ui.LayerControl.MenuOptionLabel = mol.ui.LayerControl.MenuOption.extend(
        {
            init: function(name) {
                this._super(name);
                this.setStyleName('mol-LayerControl-MenuOptionLabel');
                this.addStyleName('mol-LayerControl-MenuOption');   
                this.addStyleName('mol-LayerControl-Menu');   
            }
        }
    );
            
    /**
     * The LayerControl Display.
     */
    mol.ui.LayerControl.Display = mol.ui.Display.extend(
        {
            
            /**
             * Constructs a new LayerControl Display.
             * 
             * @param config the display configuration
             * @constructor
             */            
            init: function(config) {
                this._super('<div>');
                this.addStyleName('mol-LayerControl-Display');
                this._config = config;
                this._build();
            },

            /**
             * Public function that returns the 'Add' widget of this display.
             */
            getAddLink: function() {
                var name = this._config.text.addLayer;
                return this._menu.getOption(name).getLink();
            },

            /**
             * Public function that returns the 'Delete' widget of this display.
             */
            getDeleteLink: function() {
                var name = this._config.text.deleteLayer;
                return this._menu.getOption(name).getLink();
            },

            /**
             * Private function that builds the UI and attaches it to the 
             * root element of the display.
             */
            _build: function() {
                var element = this.getElement(),
                    addText = this._config.text.addLayer,
                    deleteText = this._config.text.deleteLayer,
                    layersText = this._config.text.layers,
                    names = [deleteText, addText];
                this._menu = new mol.ui.LayerControl.Menu(layersText);                    
                this._menu.buildOptions(names);
                this.append(this._menu);
            }
        }
    );
};


// =============================================================================
// In progress....

/**
 * LayerBuilder module that presents a widget for building a new layer
 * by selecting a type (e.g., points), source (e.g., gbif), and 
 * name (e.g., puma concolor).
 * 
 * Event binding:
 *     None
 * 
 * Event triggering:
 *     
 * AJAX calls:
 * 
 */
MOL.modules.LayerBuilder = function(mol) {
    
    mol.ui.LayerBuilder = {};

    mol.ui.LayerBuilder.Engine = mol.ui.Engine.extend(
        {
            // TODO...            
        }
    );
    
};

MOL.modules.LayerList = function(mol) {
    
    mol.ui.LayerList = {};

    mol.ui.LayerList.Display = mol.ui.Display.extend(
        {
            LayerWidget: mol.ui.Display.extend(
                {
                    init: function(config, layer) {
                    },

                    getRadioButton: function() {
                    },

                    getNameLabel: function() {
                    },
                    
                    getCheckbox: function() {
                    },

                    getInfoButton: function() {
                    },

                    getSourceButton: function() {
                    }
                }
            ),

            init: function(config) {
            },

            addLayerWidget: function(layer) {
                return new this.LayerWidget({}, layer);
            },

            deleteLayerWidget: function(layerId) {
            }
        }
    );
};
