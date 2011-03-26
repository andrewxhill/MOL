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
                switch (type) {
                case 'points':
                    switch (source) {
                    case 'gbif':
                        xhr = $.post('/api/points/gbif/'+ speciesKey);                        
                        xhr.success(
                            function(json) {
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
    mol.events.LAYER_CONTROL_ADD_LAYER = 'layer_control_add_layer';
    mol.events.LAYER_CONTROL_DELETE_LAYER = 'layer_control_delete_layer';
    mol.events.NEW_LAYER = 'new_layer';
    
    // Ripped from Backbone.js Events:
    mol.events.Bus = Class.extend(
        {
            bind : function(ev, callback) {
                var calls = this._callbacks || (this._callbacks = {});
                var list  = this._callbacks[ev] || (this._callbacks[ev] = []);
                list.push(callback);
                return this;
            },
            
            unbind : function(ev, callback) {
                var calls;
                if (!ev) {
                    this._callbacks = {};
                } else if ((calls = this._callbacks)) {
                    if (!callback) {
                        calls[ev] = [];
                    } else {
                        var list = calls[ev];
                        if (!list) return this;
                        for (var i = 0, l = list.length; i < l; i++) {
                            if (callback === list[i]) {
                                list.splice(i, 1);
                                break;
                            }
                        }
                    }
                }
                return this;
            },
            
            trigger : function(ev) {
                var list, calls, i, l;
                if (!(calls = this._callbacks)) return this;
                if (calls[ev]) {
                    list = calls[ev].slice(0);
                    for (i = 0, l = list.length; i < l; i++) {
                        list[i].apply(this, Array.prototype.slice.call(arguments, 1));
                    }
                }
                if (calls['all']) {
                    list = calls['all'].slice(0);
                    for (i = 0, l = list.length; i < l; i++) {
                        list[i].apply(this, arguments);
                    }
                }
                return this;
            }
        }    
    );
};

/**
 * Exceptions module for handling exceptions.
 */
MOL.modules.exceptions = function(mol) {
    mol.exceptions = {};
    mol.exceptions.NotImplementedError = 'NotImplementedError';
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
                mol.log.todo('App is now running');
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
                this._container = $('body');
                this._mapEngine = new mol.ui.Map.Engine(this._api, this._bus);
                this._mapEngine.start(this._container);
                this._layerControlEngine = new mol.ui.LayerControl.Engine(this._api, this._bus);
                this._layerControlEngine.start(this._container);
            },
            
            routes: {
                ":sandbox": "map"
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
                             
            _buildId: function() {
                var type = this._type,
                    source = this._source,
                    name = this._name;
                if (this._id) {
                    return this._id;                    
                }
                this.id = [type, source, name.split(' ').join('_')].join('_');
                return this.id;
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
            init: function(element) {
                this._element = element;
            },
            
            getElement: function() {
                return this._element;
            },
            
            remove: function() {
                this._element.remove();
            }
        }
    );

    /**
     * Base class for Displays.
     */
    mol.ui.Display = mol.ui.Element.extend(
        {
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
 * level events and perform AJAX calls to the server.
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
                this._bindEvents();
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
                mol.log.info('Map.Engine handling browser history change');
            },

            /**
             * Private function for binding event handles to the Bus.
             */
            _bindEvents: function() {
                var self = this;
                this._bus.bind(
                    mol.events.ADD_MAP_CONTROL,
                    function(control, position) {
                        self._display.getMapControls()[position].push(control[0]);
                    }
                ); 
                this._bus.bind(
                    mol.events.NEW_LAYER,
                    function(layer) {
                        self._display.displayLayer(layer);
                    }
                );
            }
        }
    );

    /**
     * The Map Display.
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
            },

            getMap: function() {
                return this._map;
            },

            getMapControls: function() {
                return this._map.controls;
            },

            displayLayer: function(layer) {
                var center = null,
                    marker = null,
                    circle = null,
                    coordinate = null,
                    resources = [],
                    occurrences = [],
                    point = {},
                    data = layer._json,
                    self = this;
                for (p in data.records.providers) {
                    resources = data.records.providers[p].resources;
                    for (r in resources) {
                        occurrences = resources[r].occurrences;
                        for (o in occurrences) {
                            coordinate = occurrences[o].coordinates;
                            marker = this._createMarker(coordinate);
                            //this._overlays.push(marker);                      
                            circle = this._createCircle(
                                marker.getPosition(),
                                coordinate.coordinateUncertaintyInMeters);                            
                            if (circle) {
                                //this._overlays.push(circle);
                            }     
                            point = {};
                            point.marker = marker;
                            point.circle = circle;                                
                            point.sourceUrl = data.sourceUrl;
                            point.provider = data.records.providers[p];
                            point.resource = resources[r];
                            point.occurrence = occurrences[o];
                        }
                    }
                }
            },

            _createCircle: function(center, coordinateUncertaintyInMeters) {          
                if (coordinateUncertaintyInMeters == null) {
                    return null;
                }
                var radius = parseFloat(coordinateUncertaintyInMeters),
                    opacity = 0.85,
                    circle = new google.maps.Circle(
                        {
                            map: this._map,
                            center: center,
                            radius: radius,
                            fillColor: '#CEE3F6',
                            strokeWeight: 1,                                
                            zIndex: 5
                        }
                    );
                return circle;
            },
            
            _createMarker: function(coordinate) {
                var lat = parseFloat(coordinate.decimalLatitude),
                    lng = parseFloat(coordinate.decimalLongitude),
                    center = new google.maps.LatLng(lat, lng),
                    marker = new google.maps.Marker(
                        { 
                            position: center,
                            map: this._map,
                            icon: 'http://labs.google.com/ridefinder/images/mm_20_red.png'
                        }
                    );
                return marker;
            }
        }
    );
};

/**
 * LayerControl module that presents a widget for adding or deleting layers. 
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
                    element = display.getElement(),
                    position = google.maps.ControlPosition.TOP_RIGHT;
                this._bus.trigger(mol.events.ADD_MAP_CONTROL, element, position);
                this._bindDisplay(display);
            },
            
            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.info('LayerControl.Engine handling browser history change');
            },
            
            /**
             * Private function that binds the display by setting up click
             * handlers for the 'Add' and 'Delete' buttons.
             * 
             * @param display the mol.ui.LayerControl.Display object to bind 
             */
            _bindDisplay: function(display) {
                var self = this;
                display.setEngine(this);
                this._display = display;
                display.getAddWidget().click(
                    function(event) {
                        mol.log.info('LayerControl.Engine handling Add click '
                                     + 'from LayerControl.Display');
                        self._bus.trigger(mol.events.LAYER_CONTROL_ADD_LAYER);
                    }
                );
                display.getDeleteWidget().click(
                    function(event) {
                        mol.log.info('LayerControl.Engine handling Delete click '
                                     + 'from LayerControl.Display');
                        self._bus.trigger(mol.events.LAYER_CONTROL_DELETE_LAYER);
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
                this._super($('<div>').attr({'id': 'right-controller'}));                    
                this._config = config;
                this._build();
            },

            /**
             * Public function that returns the 'Add' widget of this display.
             */
            getAddWidget: function() {
                return this._addLayer;
            },

            /**
             * Public function that returns the 'Delete' widget of this display.
             */
            getDeleteWidget: function() {
                return this._deleteLayer;
            },

            /**
             * Private function that builds the UI and attaches it to the 
             * root element of the display.
             */
            _build: function() {
                var element = this.getElement(),
                    addText = this._config.text.addLayer,
                    deleteText = this._config.text.deleteLayer,
                    layersText = this._config.text.layers;
                
                // Add Layer widget:
                this._addLayer = $('<a>')
                    .attr({'id': 'add_layer', 'href':'javascript:'});                                          
                this._addLayer.html(addText);
                
                // Delete Layer widget:
                this._deleteLayer = $('<a>')
                    .attr({'id': 'delete_layer', 'href':'javascript:'});                           
                this._deleteLayer.html(deleteText);
                
                // Options widget wraps Add/Delete layer widgets:
                this._options = $('<ul>')
                    .attr({'class': 'options list'});                    
                this._options
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'menuLabel'})
                            .html(layersText));  
                this._options
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'delete'})
                            .append(this._deleteLayer)); 
                this._options
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'add'})
                            .append(this._addLayer));               

                // Menu widget wraps Options widget:
                this._menu = $('<div>')
                    .attr({'id':'menu'})
                    .append(this._options);

                // Appends everything to the root element:
                element
                    .append(
                        $('<div>')
                            .attr({'id':'layer-widget-container', 
                                   'class':'widget-container'}))
                    .append($('<div>').attr({'id':'layers'}))
                    .append(this._menu);
            }
        }
    );
};