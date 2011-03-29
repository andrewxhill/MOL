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
                    bus = this._bus,
                    LayerEvent = mol.events.LayerEvent,
                    self = this;
                mol.log.info('Api sending AJAX request for layer ' + layer.getId());
                switch (type) {
                case 'points':
                    switch (source) {
                    case 'gbif':
                        xhr = $.post('/api/points/gbif/'+ speciesKey);                        
                        xhr.success(
                            function(json) {
                                var layer = new mol.model.Layer(type, source, name, json);

                                success(json);
                                
                                bus.fireEvent(new LayerEvent({action: 'new', layer: layer}));
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
    
    /**
     * Base class for events. Events can be fired on the event bus.
     */
    mol.events.Event = Class.extend(
        {
            /**
             * Constructs a new event.
             * 
             * @param type the type of event
             */
            init: function(type, action) {
                var IllegalArgumentException = mol.exceptions.IllegalArgumentException;
                if (!type) {
                    throw IllegalArgumentException;
                }
                this._type = type;
                this._action = action;
            },

            /**
             * Gets the event type.
             * 
             * @return the event type string
             */
            getType: function() {
                return this._type;
            },

            /**
             * Gets the action.
             * 
             * @return action
             */
            getAction: function() {
                return this._action;
            }            
        }
    );

    /**
     * Event for colors.
     */
    mol.events.ColorEvent = mol.events.Event.extend(
        {
            init: function(config) {
                this._super('ColorEvent', config.action);
                this._color = config.color;
                this._category = config.category;
                this._id = config.id;
            },
            
            getColor: function() {
                return this._color;
            },
            
            getCategory: function() {
                return this._category;
            },

            getId: function() {
                return this._id;
            }            
        }
    );
    mol.events.ColorEvent.TYPE = 'ColorEvent';

    /**
     * Event for layers.
     */
    mol.events.LayerEvent = mol.events.Event.extend(
        {
            init: function(config) {
                this._super('LayerEvent', config.action);
                this._layer = config.layer;
            },

            getLayer: function() {
                return this._layer;
            }
        }
    );
    mol.events.LayerEvent.TYPE = 'LayerEvent';

    /**
     * Trigger this event if you generate layer control actions such as 'Add' 
     * or 'Delete'.
     * 
     * Supported actions:
     *     add-click
     *     delete-click   
     */
    mol.events.LayerControlEvent = mol.events.Event.extend(
        {
            init: function(action) {
                this._super('LayerControlEvent', action);
            }            
        }
    );
    mol.events.LayerControlEvent.TYPE = 'LayerControlEvent';

    /**
     * Trigger this event to add a map control widget on the map at a position.
     */
    mol.events.MapControlEvent = mol.events.Event.extend(
        {
            /**
             * Constructs a new MapControlEvent object.
             * 
             * @constructor
             * 
             * @param div - the div element of the control to display on the map
             * @param position - the google.maps.ControlPosition
             * @param action - the action (add, remove)
             */
            init: function(div, position, action) {
                this._super('MapControlEvent');
                this._div = div;
                this._position = position;
                this._action = action;
            },
            
            /**
             * Gets the widget.
             * 
             * @return widget
             */
            getDiv: function() {
                return this._div;
            },

            /**
             * Gets the position.
             * 
             * @return position
             */
            getPosition: function() {
                return this._position;
            },

            /**
             * Gets the action.
             * 
             * @return action
             */
            getAction: function() {
                return this._action;
            }
        }
    );
    mol.events.MapControlEvent.TYPE = 'MapControlEvent';

    
    // Event types:
    mol.events.ADD_MAP_CONTROL = 'add_map_control';


    mol.events.NEW_LAYER = 'new_layer';
    mol.events.DELETE_LAYER = 'delete_layer';
//    mol.events.SET_LAYER_COLOR = 'set_layer_color';
    mol.events.GET_NEXT_COLOR = 'get_next_color';
    mol.events.NEXT_COLOR = 'next_color';
    mol.events.COLOR_CHANGE = 'color_change';
    
    /**
     * The event bus.
     */
    mol.events.Bus = function() {
        if (!(this instanceof mol.events.Bus)) {
            return new mol.events.Bus();
        }
        _.extend(this, Backbone.Events);

        /**
         * Fires an event on the event bus.
         * 
         * @param event the event to fire
         */
        this.fireEvent = function(event) {
            this.trigger(event.getType(), event);
        };

        /**
         * Adds an event handler for an event type.
         * 
         * @param type the event type
         * @param handler the event handler callback function
         */
        this.addHandler = function(type, handler) {
            this.bind(
                type, 
                function(event) {
                    handler(event);
                }
            );
        };
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

                this._searchEngine = new mol.ui.Search.Engine(this._api, this._bus);
                this._searchEngine.start(this._container);
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
                this._icon = null;
                this._buildId();
            },
            
            getIcon: function() {
                return this._icon;
            },
            
            setIcon: function(icon) {
                this._icon = icon;
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
                this._bindEvents();
            },
            
            _bindEvents: function() {
                var bus = this._bus,
                    ColorEvent = mol.events.ColorEvent;
                
                bus.addHandler(
                    ColorEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            category = event.getCategory(),
                            id = event.getId(),
                            color = null,
                            config = {
                                action: 'change',
                                color: null,
                                category: category,
                                id: id
                            };
                        
                        switch (action) {
         
                        case 'get':
                            switch (category) {
                                
                            case 'points':
                                // TODO(andrew): Logic for getting next color.
                                config.color = new mol.core.ColorSetter.Color(55, 133, 233);
                                bus.fireEvent(new ColorEvent(config));
                                break;
                            }
                            
                        }
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
                if (!element) {
                    element = '<div>';
                }
                this._element = $(element);
            },
            
            /**
             * Returns the underlying DOM element object.
             */
            getElement: function() {
                return this._element;
            },
            
            /**
             * Proxies to JQuery.
             */
            isVisible: function() {
                if (!this._element.is(':visible')) {
                    return false;
                }
                return true;
            },

            /**
             * Proxies to JQuery.show()
             */
            show: function() {
                this._element.show();
            },
            
            /**
             * Proxies to JQuery.hide()
             */
            hide: function() {
                this._element.hide();                
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
                this._points = {};
                this._layers = {};
                this._controlDivs = {};
                this._canvasSupport = false;
                if ( !!document.createElement('canvas').getContext ) {
                    this._iconHeight = 15;
                    this._iconWidth = 15;
                    this._canvasSupport = true;
                    this._markerCanvas = new mol.ui.Map.MarkerCanvas(this._iconWidth,this._iconHeight);
                    this._markerContext = this._markerCanvas.getContext();
                    this._iconLayers = {
                        background: new Image(),
                        foreground: new Image(),
                        error: new Image()
                    };
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
                this._bindDisplay(new mol.ui.Map.Display(), container);
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
            },

            /**
             * Adds an event handler for new layers.
             */
            _addLayerEventHandler: function() {
                var bus = this._bus,
                    LayerEvent = mol.events.LayerEvent,
                    ColorEvent = mol.events.ColorEvent,
                    deleteLayer = this._deleteLayer,
                    layers = this._layers;
                
                bus.addHandler(
                    LayerEvent.TYPE,
                    function(event) {
                        var layer = event.getLayer(),
                            lid = layer.getId(),
                            action = event.getAction(),
                            config = {
                                action: 'get',
                                category: 'points',
                                id: lid
                            };
                        
                        switch (action) {

                        case 'new':
                            layers[lid] = layer;
                            // We need a layer color before displaying it:
                            bus.fireEvent(new ColorEvent(config));
                            break;

                        case 'delete':
                            deleteLayer(lid);
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
                    controlDivs = this._controlDivs;
                                
                bus.addHandler(
                    MapControlEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            div = event.getDiv(),
                            position = event.getPosition();

                        switch (action) {

                        case 'add':
                            // push(div) returns the length of the controls 
                            // array. So push(div) - 1 is the div index in the 
                            // controls array. We need the div index if we want
                            // to later remove the div control from the map.
                            controlDivs[div] = controls[position].push(div) - 1;
                            break;

                        case 'remove':
                            if (controlDivs[div]) {
                                controls.removeAt(controlDivs[div]);
                                delete controlDivs[div];
                            }                            
                        }
                    }
                );
            },

            _addColorEventHandler: function() {
                var ColorEvent = mol.events.ColorEvent,
                    bus = this._bus,
                    points = this._points,
                    layers = this._layers,
                    self = this;
                
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
                                // TODO
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
                    iconUrl = urls.iconUrl,
                    w = this._iconWidth,
                    h = this._iconHeight,
                    point = null,
                    image = new google.maps.MarkerImage(iconUrl, new google.maps.Size(w, h));
                
                switch (type) {

                case 'points':
                    for (x in points) {
                        point = points[x];
                        if (point instanceof google.maps.Marker) {
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
                    points = this._points[layerId],
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
                var background = this._iconLayers.background,
                    foreground = this._iconLayers.foreground,
                    error = this._iconLayers.error,
                    ctx = this._markerContext,
                    canvas = this._markerCanvas,
                    w = this._iconWidth,
                    h = this._iconHeight,
                    url = null,
                    errorUrl = null;
                if (!this._canvasSupport) {
                    return {iconUrl: icon.src, iconErrorUrl: icon.src};
                }
                ctx.drawImage(background, 0, 0, w, h);
                ctx.drawImage(icon, 0, 0, w, h);
                ctx.drawImage(foreground, 0, 0, w, h);
                url = canvas.getDataURL();
                ctx.drawImage(error, 0, 0, w, h);
                errorUrl = canvas.getDataURL();
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
                for (p in data.records.providers) {
                    resources = data.records.providers[p].resources;
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
                    w = this._iconWidth,
                    h = this._iconHeight,
                    image = new google.maps.MarkerImage(iconUrl, new google.maps.Size(w, h)),
                    marker = new google.maps.Marker(
                        { 
                            position: center,
                            map: map,
                            icon: image
                        }
                    );
                return marker;
            }
        }
    );

    /**
     * The top level placemark canvas container
     */
    mol.ui.Map.MarkerCanvas = mol.ui.Element.extend(
        {
            init: function(width,height) {
                this._super('<canvas width='+width+' height='+height+'>');
                this.setStyleName('mol-MarkerCanvas');
                this._ctx = this.getElement()[0].getContext("2d");
            },

            getContext: function() {
                return this._ctx;
            },

            getDataURL: function(){
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
                    rightPosition = google.maps.ControlPosition.TOP_RIGHT,
                    centerPosition = google.maps.ControlPosition.TOP_CENTER;
                this._id = 'map';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
                this._map = new google.maps.Map($('#' + this._id)[0], mapOptions);
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
                    display = new mol.ui.LayerControl.Display(config);
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
                mol.log.todo('LayerControl.Engine.go()');
            },
            
            /**
             * Private function that binds the display by setting up click
             * handlers for the 'Add' and 'Delete' buttons.
             * 
             * @param display the mol.ui.LayerControl.Display object to bind 
             */
            _bindDisplay: function(display) {
                var bus = this._bus,
                    div = display.getElement()[0],
                    position = google.maps.ControlPosition.TOP_RIGHT,
                    LayerControlEvent = mol.events.LayerControlEvent,
                    MapControlEvent = mol.events.MapControlEvent;

                this._display = display;
                display.setEngine(this);                
                
                bus.fireEvent(new MapControlEvent(div, position, 'add'));

                display.getAddLink().click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('add-click'));
                    }
                );

                display.getDeleteLink().click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('delete-click'));
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
     * The top right map control container. It gets added to the Google map as a
     * control. 
     */
    mol.ui.LayerControl.RightController = mol.ui.Element.extend(
        {
            init: function() {
                this._super('<div>');
                this.addStyleName('mol-LayerControl-Display');
            }
        }
    );

    /**
     * The container for Layers, Filters, Tools, and other control widgets on
     * the map. Its parent is RightController.
     */
    mol.ui.LayerControl.WidgetContainer = mol.ui.Element.extend(
        {
            init: function() {
                this._super('<div>');
                this.setStyleName('mol-WidgetContainer');
            },

            setWidget: function(widget) {
                this.append(widget);
            }
        }        
    ),

            
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
                this.setStyleName('mol-RightController');
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
                this._widgetContainer = new mol.ui.LayerControl.WidgetContainer();
                this.append(this._widgetContainer);
                this._menu = new mol.ui.LayerControl.Menu(layersText);                    
                this._menu.buildOptions(names);
                this._widgetContainer.append(this._menu);
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
    
    /**
     * The LayerList engine.
     */
    mol.ui.LayerList.Engine = mol.ui.Engine.extend(
        {
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
                var config = this._layerWidgetConfig(),
                    display = new mol.ui.LayerList.Display(config),
                    bus = this._bus,
                    self = this;
                display.setEngine(this);
                // On new layer events add a LayerWidget to the display
                // and wire up events:
                this._bus.bind(
                    mol.events.NEW_LAYER,
                    function(layer) {
                        var layerWidget = self._display.addLayerWidget(layer, config);
                        layerWidget.setEngine(self);
                        layerWidget.getRadioButton().click(
                            self._bus.trigger(
                                mol.events.LAYER_SELECTED, 
                                layer.getId()));
                        // TODO: Add click handlers for all controls...
                    }
                );
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
            
            _layerWidgetConfig: function() {
                // TODO
                return {
                };                
            }
        }
    );

    /**
     * The LayerWidget.
     */
    mol.ui.LayerList.LayerWidget = mol.ui.Display.extend(
        {
            init: function(layer, config) {
                this._super('<div>');
                this.setStyleName('mol-LayerList-LayerWidget');
            },

            getLayerId: function() {                
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
    
    /**
     * The LayerList display.
     */
    mol.ui.LayerList.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super('<div>');
                this.setStyleName('mol-LayerList-Display');
                this._widgets = {};
            },

            /**
             * Add a layer widget to the list.
             * 
             * @param layer the layer to add
             * @param config the layer widget config 
             */
            addLayerWidget: function(layer, config) {                
                var layerWidget = null,
                    lid = layer.getId();
                if (this._widgets[lid]) {
                    return;
                }
                layerWidget = new mol.ui.LayerList.LayerWidget({}, layer);
                this._widgets[lid] = layerwidget;
                this.append(layerWidget);                
            },

            /**
             * Deletes a layer widget from the list.
             * 
             * @param layerId the id of the layer to delete
             */
            deleteLayerWidget: function(layerId) {
                var layerWidget = this._widgets[layerId];
                if (!layerWidget) {
                    return;
                }
                layerWidget.remove();
                delete this._widgets[layerId];
            }
        }
    );
};

/**
 * Search module has a display used as a map control. It allows users to search
 * for layers to add to the map.
 */
MOL.modules.Search = function(mol) {
    
    mol.ui.Search = {};

    /**
     * The search engine.
     */
    mol.ui.Search.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs the engine.
             * 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
            },

            /**
             * Starts the engine by creating and binding the display.
             *
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                this._bindDisplay(new mol.ui.Search.Display({}));
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('Search.Engine.go()');
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display) {                
                this._display = display;
                display.setEngine(this);

                display.hide();

                this._addLayerControlEventHandler();                

                // TODO: Set up handlers for DOM elements in the display.

                this._addDisplayToMap();
            },
            
            /**
             * Fires a MapControlEvent so that the display is attached to
             * the map as a control in the TOP_LEFT position.
             */
            _addDisplayToMap: function() {
                var MapControlEvent = mol.events.MapControlEvent,
                    div = this._display.getElement()[0],
                    position = google.maps.ControlPosition.TOP_CENTER,
                    action = 'add';
                bus.fireEvent(new MapControlEvent(div, position, action));     
            },

            /**
             * Adds an event handler for LayerControlEvent events so that a
             * 'add-click' action will show the search display as a control
             * on the map.
             */
            _addLayerControlEventHandler: function() {
                var display = this._display,
                    bus = this._bus,
                    LayerControlEvent = mol.events.LayerControlEvent;
                
                bus.addHandler(
                    LayerControlEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            displayNotVisible = !display.isVisible();               
                        
                        if (action === 'add-click' && displayNotVisible) {
                            display.show();
                        }
                    }
                );
            }
        }
    );
    
    /**
     * The search display.
     */
    mol.ui.Search.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super('<div>Search.Display</div>');
                this.setStyleName('mol-Search-Display');
                this._config = config;
            }
        }
    );
};
