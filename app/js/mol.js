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
    mol.events.DELETE_LAYER = 'delete_layer';
    
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
                this._layerControlEngine = new mol.ui.LayerMenu.Engine(this._api, this._bus);
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
                this._id = [type, source, name.split(' ').join('_')].join('_');
                return this._id;
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
                this.addStyleName(this.getPrimaryStyleName() + '-' + styleSuffix);
            },         

            /**
             * Gets all of the object's style names, as a space-separated list.
             */
            getStyleName: function() {
                return this.getElement().attr('class').split(/\s+/).join(' ');
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
                oldStyle = this.getStyleName(elem);
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
                        if (oldStyle.length() > 0) {
                            oldStyle += " ";
                        }
                        this.setStyleName(oldStyle + style);
                    }
                } else {
                    // Don't try to remove the style if it's not there.
                    if (idx != -1) {
                        // Get the leading and trailing parts, without the removed name.
                        begin = oldStyle.substring(0, idx).trim();
                        end = oldStyle.substring(idx + style.length()).trim();

                        // Some contortions to make sure we don't leave extra spaces.
                        if (begin.length() == 0) {
                            newClassName = end;
                        } else if (end.length() == 0) {
                            newClassName = begin;
                        } else {
                            newClassName = begin + " " + end;
                        }
                        this.setStyleName(newClassName);
                    }
                }
            },

             /**
              * Replaces all instances of the primary style name with newPrimaryStyleName.
              * 
              * TODO: Use JQuery here for CB stuff?
              */
            _updatePrimaryAndDependentStyleNames: function(elem, newPrimaryStyle) {
                var classes = elem.className.split(/\s+/);
                if (!classes) {
                    return;
                }                
                var oldPrimaryStyle = classes[0];
                var oldPrimaryStyleLen = oldPrimaryStyle.length;                
                classes[0] = newPrimaryStyle;
                for (var i = 1, n = classes.length; i < n; i++) {
                    var name = classes[i];
                    if (name.length > oldPrimaryStyleLen
                        && name.charAt(oldPrimaryStyleLen) == '-'
                        && name.indexOf(oldPrimaryStyle) == 0) {
                        classes[i] = newPrimaryStyle + name.substring(oldPrimaryStyleLen);
                    }
                }
                elem.className = classes.join(" ");
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
             * Private function for binding event handles.
             */
            _bindEvents: function() {
                var self = this;
                // Adds a control to the map:
                this._bus.bind(
                    mol.events.ADD_MAP_CONTROL,
                    function(control, type) {
                        var div = self._display.getRightControl();
                        switch (type) {
                        case mol.ui.Map.Display.ControlType.LAYER:
                            div.remove(mol.ui.Map.Display.ControlType.LAYER);
                            div.find('#layer-widget-container').append(control);
                            break;
                        }
                    }
                ); 
                // Displays a new layer on the map:
                this._bus.bind(
                    mol.events.NEW_LAYER,
                    function(layer) {
                        self._displayLayer(layer);
                    }
                );
                // Deletes a layer on the map.
                this._bus.bind(
                    mol.events.DELETE_LAYER,
                    function(layerId) {
                        self._deleteLayer(layerId);
                    }
                );
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
                    data = layer._json;
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
                },
                    position = google.maps.ControlPosition.TOP_RIGHT;
                this._id = 'map';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
                this._map = new google.maps.Map($('#' + this._id)[0], mapOptions);
                this._rightControl = $('<div>')
                    .attr({'id': 'right-controller'})
                    .append($('<div>')                    
                            .attr({'id':'layer-widget-container', 
                                   'class':'widget-container'}));
                this._map.controls[position].push(this._rightControl[0]);              
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

            getRightControl: function() {
                return this._rightControl;
            }
        }
    );
};

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
            
        }
    );
    
};

/**
 * LayerMenu module that presents a widget for adding or deleting layers. 
 * It can handle app level events and perform AJAX calls to the server.
 * 
 * Event binding:
 *     None
 * 
 * Event triggering:
 *     ADD_LAYER - Triggered when the Add widget is clicked
 *     DELETE_LAYER - Triggered when the Delete widget is clicked
 */
MOL.modules.LayerMenu = function(mol) {

    mol.ui.LayerMenu = {};

    /**
     * The LayerMenu Engine.
     */
    mol.ui.LayerMenu.Engine = mol.ui.Engine.extend(
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
                    display = new mol.ui.LayerMenu.Display(config),
                    element = display.getElement(),
                    position = google.maps.ControlPosition.TOP_RIGHT,
                    bus = this._bus;
                bus.trigger(
                    mol.events.ADD_MAP_CONTROL,                     
                    element, 
                    mol.ui.Map.Display.ControlType.LAYER);
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
                mol.log.info('LayerMenu.Engine handling browser history change');
            },
            
            /**
             * Private function that binds the display by setting up click
             * handlers for the 'Add' and 'Delete' buttons.
             * 
             * @param display the mol.ui.LayerMenu.Display object to bind 
             */
            _bindDisplay: function(display) {
                var self = this;
                this._display = display;
                display.setEngine(this);
                display.getAddWidget().click(
                    function(event) {
                        self._bus.trigger(mol.events.LAYER_CONTROL_ADD_LAYER);
                    }
                );
                display.getDeleteWidget().click(
                    function(event) {
                        self._bus.trigger(mol.events.LAYER_CONTROL_DELETE_LAYER);
                    }
                );
            },

            /**
             * Private function that returns a configuration object for the 
             * mol.ui.LayerMenu.Display object.
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
    
    mol.ui.LayerMenu.OptionWidget =  mol.ui.Element.extend(
        {
            init: function(name) {
                this._super($('<li>').attr({'class':'option list'}));
                this.getElement()
                    .append($('<a>'))
                    .attr({'href': 'javascript:'})
                    .html(name);
            }
        }
    );
            
    mol.ui.LayerMenu.MenuWidget = mol.ui.Element.extend(
        {
            init: function(names) {
                this._super($('<div>').attr({'class':'layer-menu'}));
                this._options = {};
                var name = null,
                    element = this.getElement(),
                    menu = $('<ul>').attr({'class': 'options list'}),
                    option = null;                    
                for (x in names) {
                    name = names[x];
                    option = new mol.ui.LayerMenu.OptionWidget(name);
                    this._options[name] = option;
                    menu.append(option.getElement());
                }
                element.append(menu);
            },

            getOptionWidget: function(name) {
                return this._options[name].getElement();
            }
        }
    );
    
    /**
     * The LayerMenu Display.
     */
    mol.ui.LayerMenu.Display = mol.ui.Display.extend(
        {
            
            /**
             * Constructs a new LayerMenu Display.
             * 
             * @param config the display configuration
             * @constructor
             */            
            init: function(config) {
                this._super($('<div>').attr({'id':'layers'}));
                this._config = config;
                this._build();
            },

            /**
             * Public function that returns the 'Add' widget of this display.
             */
            getAddWidget: function() {
                return this._menuWidget.getOptionWidget(this._config.text.addLayer);
            },

            /**
             * Public function that returns the 'Delete' widget of this display.
             */
            getDeleteWidget: function() {
                return this._menuWidget.getOptionWidget(this._config.text.deleteLayer);
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
                    names = [layersText, deleteText, addText];
                this._menuWidget = new mol.ui.LayerMenu.MenuWidget(names);
                element.append(this._menuWidget.getElement());
                                            
                //element.append(this._menuWidget());
                //element.append(this._listWidget());
            },

            _listWidget: function() {
                this._list = $('<div>')
                    .sortable({items: '.layer', cursor: 'move'});
                return this._list;
            },

            _menuWidget: function() {
                var element = this.getElement(),
                    addText = this._config.text.addLayer,
                    deleteText = this._config.text.deleteLayer,
                    layersText = this._config.text.layers;                

                this._menu = $('<div>').attr({'id':'menu'});                    

                // The Add link:
                this._addLayer = $('<a>')
                    .attr({'id': 'add_layer', 'href':'javascript:'});                                          
                this._addLayer.html(addText);
                
                // The Delete link:
                this._deleteLayer = $('<a>')
                    .attr({'id': 'delete_layer', 'href':'javascript:'});                           
                this._deleteLayer.html(deleteText);
                
                // The options list:
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

                // Menu wraps the options list:
                this._menu.append(this._options);
               
                return this._menu;
            }
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