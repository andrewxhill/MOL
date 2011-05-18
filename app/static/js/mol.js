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

MOL.src = {};

MOL.src.makeId = function() {
    var text = "",
        possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for( var i=0; i < 5; i++ ) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
};

MOL.src.files = [
    'mol.app.js?id=' + MOL.src.makeId(), 
    'mol.events.js?id=' + MOL.src.makeId(), 
    'mol.ajax.js?id=' + MOL.src.makeId(), 
    'mol.log.js?id=' + MOL.src.makeId(), 
    'mol.exceptions.js?id=' + MOL.src.makeId(), 
    'mol.location.js?id=' + MOL.src.makeId(), 
    'mol.model.js?id=' + MOL.src.makeId(), 
    'mol.util.js?id=' + MOL.src.makeId(),
    'mol.ui.js?id=' + MOL.src.makeId(),
    'mol.ui.ColorSetter.js?id=' + MOL.src.makeId(), 
    'mol.ui.LayerControl.js?id=' + MOL.src.makeId(), 
    'mol.ui.LayerList.js?id=' + MOL.src.makeId(), 
    'mol.ui.Map.js?id=' + MOL.src.makeId(), 
    'mol.ui.Search.js?id=' + MOL.src.makeId(),
    'mol.ui.Metadata.js?id=' + MOL.src.makeId()
];

/**
 * Dynamically loads JavaScript source modules by creating script elements and 
 * appending them to DOM in the head element.
 */
MOL.src.load = function() {
    var src = MOL.src.files,
        file = null,
        script = null;
    for (x in src) {
        file = "../../../js/" + src[x];
        script = document.createElement('script');
        script.setAttribute("type","text/javascript");
        script.setAttribute("src", file);
        document.getElementsByTagName("head")[0].appendChild(script);
    }
};
















/**
 * App module for running the app with a given configuration.
 */
MOL.modules.app = function(mol) {

    mol.app = {};

    mol.app.Instance = Class.extend(
        {
            init: function(config) {
                mol.log.enabled = config ? config.logging: false;
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
            init: function(action, layerId) {
                this._super('LayerControlEvent', action);
                this._layerId = layerId;
            },
            
            getLayerId: function() {
                return this._layerId;
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
             * @param div - the div element of the display to add to map control
             * @param controlPosition - mol.ui.Map.Control.ControlPosition
             * @param displayPosition - mol.ui.Map.Control.DisplayPosition
             * @param action - the action (add, remove)
             */
            init: function(config) {
                this._super('MapControlEvent');
                this._display = config.display;
                this._controlPosition = config.controlPosition;
                this._displayPosition = config.displayPosition;
                this._action = config.action;
            },
            
            /**
             * Gets the widget.
             * 
             * @return widget
             */
            getDisplay: function() {
                return this._display;
            },

            /**
             * Gets the control position.
             * 
             * @return controlPosition
             */
            getControlPosition: function() {
                return this._controlPosition;
            },

            /**
             * Gets the display position within the control.
             */
            getDisplayPosition: function() {
                return this._displayPosition;                
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
 * AJAX module for communicating with the server. Contains an Api object that 
 * can be used to execute requests paired with success and failure callbacks.
 */
MOL.modules.ajax = function(mol) {
    mol.ajax = {};
    
    /**
     * Action.
     */
    mol.ajax.Action = Class.extend(
        {
            init: function(name, type, params) {
                this.name = name;
                this.type = type;
                this.params = params || {};
            },
            
            toJson: function() {
                return JSON.stringify(this);
            },

            getName: function() {
                return this.name;
            },
            
            getType: function() {
                return this.type;
            },

            getParams: function() {
                return this.params;
            }
        }
    );

    /**
     * ActionCallback.
     */
    mol.ajax.ActionCallback = Class.extend(
        {
            init: function(success, failure) {
                this._success = success;
                this._failure = failure;
            },

            /**
             * @param error - the mol.exceptions.Error that caused failure
             */
            onFailure: function(error) {
                this._failure(error);
            },
            
            /**
             * @param actionResponse - the mol.ajax.ActionResponse for the action
             */
            onSuccess: function(actionResponse) {
                this._success(actionResponse);
            }
        }
    );

    
    /**
     * The layer action.
     */
    mol.ajax.LayerAction = mol.ajax.Action.extend(
        {
            /**
             * @param type - the action type (only 'search' for now)
             */
            init: function(type, params) {
                this._super('LayerAction', type, params);                
            }
        }
    );
    


    /**
     * The AJAX API.
     */
    mol.ajax.Api = Class.extend(
        {
            /**
             * Constructs a new Api object with an event bus.
             * 
             * @param bus mol.events.Bus
             * @constructor
             */
            init: function(bus) {
                this._bus = bus;
            },
            
            /**
             * Executes an action asynchronously.
             * 
             * @param action the mol.ajax.Action
             * @param callback the mol.ajax. ActionCallback
             */
            execute: function(action, callback ) {
                var params = {action: action.toJson()},
                    xhr = $.post('/webapp', params, 'json'),
                    self = this;

                xhr.success(
                    function(response) {
                        callback.onSuccess(response);
                        self.fireEvents(action);
                    }
                );

                xhr.error(
                    function(error) {
                        callback.onFailure(error);
                    }
                );
            },

            fireEvents: function(action) {
                var bus = this._bus,
                    actionName = action.getName(),
                    actionType = action.getType();

                switch (actionName) {

                case 'LayerAction':
                    switch (actionType) {

                    case 'search':
                        mol.log.todo('Fire LayerEvent');                        
                    }
                }                        
            }
        }
    );    
};

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
 * Exceptions module for handling exceptions.
 */
MOL.modules.exceptions = function(mol) {
    mol.exceptions = {};
    
    mol.exceptions.Error = Class.extend(
        {
            init: function(msg) {
                this._msg = msg;
            },

            getMessage: function() {
                return this._msg;
            }
        }
    );

    mol.exceptions.NotImplementedError = mol.exceptions.Error.extend(
    );

    mol.exceptions.IllegalArgumentException = mol.exceptions.Error.extend(
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
                this._colorSetter = new mol.ui.ColorSetter.Api({'bus': this._bus});
                this._container = $('body');

                this._mapEngine = new mol.ui.Map.Engine(this._api, this._bus);
                this._mapEngine.start(this._container);

                this._layerControlEngine = new mol.ui.LayerControl.Engine(this._api, this._bus);
                this._layerControlEngine.start(this._container);                

                this._searchEngine = new mol.ui.Search.Engine(this._api, this._bus);
                this._searchEngine.start(this._container);
                
                this._metadataEngine = new mol.ui.Metadata.Engine(this._api,this._bus);
                this._metadataEngine.start(this._container);
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

    mol.model.Model = Class.extend(
        {           
            init: function(props) {
                this._props = props;
            },

            get: function(name) {
                return this._props[name];
            },

            toJson: function() {
                return JSON.stringify(this._props);
            }
        }
    );

    mol.model.LayerSource = mol.model.Model.extend(
        {
            init: function(props) {
                this._super(props);
            },

            getId: function() {
                return this.get('id');
            },

            getNames: function() {
                return this.get('names');
            },

            getTypes: function() {
                return this._get('types');
            }
        }
    );

    /**
     * The layer model.
     */
    mol.model.Layer = Class.extend(
        {
            init: function(params) {
                this._type = params.type;
                this._source = params.source;
                this._name = params.name;
                this._name2 = params.name2;
                this._key_name = params.key_name;
                this._json = params.json;
                this._color = null;
                this._icon = null;
            },

            hasPoints: function() {
                // TODO                
            },

            hasRange: function() {
                // TODO
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
            
            getSubName: function() {
                return this._name2;                
            },

            getKeyName: function() {
                return this._key_name;                
            },
            
            getId: function() {
                return this._key_name;
            },
            
            getColor: function() {
                return this._color;                
            },
            
            setColor: function(color) {
                this._color = color;
            }
        }
    );
};
/**
 * Utilities.
 */
MOL.modules.util = function(mol) {
    mol.util = {};
    
    mol.util. urlEncode = function(obj) {
        var str = [];
        for(var p in obj)
            str.push(p + "=" + encodeURIComponent(obj[p]));
        return str.join("&");
    };
};/**
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
            change: function(handler) {
                this._element.change(handler);
            },
            
            attr: function(name, val) {
                if (val === undefined) {
                    return this._element.attr(name);
                } else {
                    return this._element.attr(name, val);                    
                }
            },

            /**
             * Proxies to JQuery to find parent element.
             */
            getParent: function(){
                return new mol.ui.Element(this._element.parent());
            },
            
            /**
             * Proxies to JQuery to find child element.
             */
            findChild: function(identfier){
                return new mol.ui.Element(this._element.find(identfier));
            },

            findChildren: function(id) {
                var res = new Array();
                this._element.children(id).each(function(c,v){
                    res.push(new mol.ui.Element(v));
                });
                return res;
            },

            text: function(text) {
                if (text) {
                    this._element.text(text);
                    return true;
                } else {
                    return this._element.text();
                }
            },

            /**
             * Proxies to JQuery.
             */
            val: function(val) {
                if (val) {
                    this._element.val(val);
                    return true;
                } else {
                    return this._element.val();    
                }                
            },
            
            /**
             * Proxies to JQuery.
             */
            setInnerHtml: function(html) {
                this._element.html(html);
            },

            /**
             * Proxies to JQuery.
             */
            getInnerHtml: function() {
                var html = this._element.html();
                return html;
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

            setChecked: function(checked) {
                this.attr('checked', checked);
            },

            isChecked: function() {
                if (!this._element.is(':checked')) {
                    return false;
                }
                return true;
            },
            
            /**
             * Proxies to JQuery UI.
             */
            disableSelection: function() {
                this._element.selectable({ disabled: true });
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

            keyup: function(handler) {
                this._element.keyup(handler);
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

            focus: function() {
                this._element.focus();
            },
            
            fadeout: function(n) {
                var self = this;
                this._element.animate({opacity:0},3000,'swing', function(){self._element.remove()});
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
 * TODO: Andrew
 */
MOL.modules.ColorSetter = function(mol) {
    
    mol.ui.ColorSetter = {};
    
    mol.ui.ColorSetter.Color = Class.extend(
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

    mol.ui.ColorSetter.Api = Class.extend(
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
                                config.color = new mol.ui.ColorSetter.Color(32, 40, 73);
                                break;

                            case 'range':
                                config.color = new mol.ui.ColorSetter.Color(83, 42, 16);
                                break;
                            case 'ecoregion':
                                config.color = new mol.ui.ColorSetter.Color(131, 209, 6);
                                break;
                            case 'pa':
                                config.color = new mol.ui.ColorSetter.Color(44, 6, 209);
                                break;
                            }                            
                            bus.fireEvent(new ColorEvent(config));
                        }                        
                    }
                );
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
     * The Layer engine.
     */
    mol.ui.LayerControl.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs the engine.
             * 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
                this._layerIds = {};
            },

            /**
             * Starts the engine by creating and binding the display.
             *
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                this._bindDisplay(new mol.ui.LayerControl.Display());
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('LayerControl.Engine.go()');
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display, text) {                
                var self = this,
                    LayerControlEvent = mol.events.LayerControlEvent,
                    LayerEvent = mol.events.LayerEvent,
                    widget = null,
                    bus = this._bus, 
                    ch = null,
                    styles = null,
                    layerId = null;


                this._display = display;
                display.setEngine(this);            
                
                // Clicking the add button fires a LayerControlEvent:
                widget = display.getAddButton();
                widget.click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('add-click'));
                    }
                );

                // Clicking the delete button fires a LayerControlEvent:
                widget = display.getDeleteButton();
                widget.click(
                    function(event) {
                        ch = new mol.ui.Element($('.layer.widgetTheme.selected')[0]);
                        layerId = ch.attr('id');
                        ch.remove();
                        bus.fireEvent(new LayerControlEvent('delete-click', layerId));
                        delete self._layerIds[layerId];
                    }
                );
                
                this._addDisplayToMap();

                bus.addHandler(
                    LayerEvent.TYPE, 
                    function(event) {
                        var action = event.getAction(),
                            layer = event.getLayer(),
                            layerId = layer.getKeyName(),
                            layerType = layer.getType(),
                            layerName = layer.getName(),
                            layerSubName = layer.getSubName(),
                            layerIds = self._layerIds,
                            layerUi = null,
                            display = self._display,
                            LayerEvent = mol.events.LayerEvent,
                            ch = null,
                            widget = null;
                    
                        switch (action) {                                                       
    
                        case 'add':
                            if (layerIds[layerId]) {
                                // Duplicate layer.
                                return;
                            }
                            layerIds[layerId] = true;
                            layerUi = display.getNewLayer();
                            layerUi.getName().text(layerName);
                            //layerUi.getSubName().text(layerSubName);
                            layerUi.getType().attr("src","/static/maps/search/"+ layerType +".png");
                            layerUi.attr('id', layerId);
                            
                            var ntst = function(){f = "/static/config/nulltest.js"; s = document.createElement('script'); s.setAttribute("type","text/javascript"); s.setAttribute("src", f); document.getElementsByTagName("head")[0].appendChild(s) };
                            nullTest = (layerId == 'points/gbif/13816451') ? ntst() : function(){};

                            layerUi.click(function(e) {
                                ch = new mol.ui.Element(e.target).getParent().findChildren('.layer');
                                for (y in ch) {
                                    ch[y].removeStyleName('selected');
                                }
                                new mol.ui.Element(e.target).addStyleName('selected');
                            });
                            
                            widget = layerUi.getToggle();
                            widget.setChecked(true);
                            widget.click(
                                function(event) {
                                    console.log(widget);
                                    bus.fireEvent(
                                        new LayerEvent(
                                            {
                                                action: widget.isChecked() ? 'checked': 'unchecked',
                                                layer: layer
                                            }
                                        )
                                    );
                                }
                            );
                            break;
                        }
                    }
                );
            },

            /**
             * Fires a MapControlEvent so that the display is attached to
             * the map as a control in the TOP_LEFT position.
             */
            _addDisplayToMap: function() {
                var MapControlEvent = mol.events.MapControlEvent,
                    display = this._display,
                    bus = this._bus,
                    DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    ControlPosition = mol.ui.Map.Control.ControlPosition,
                    action = 'add',
                    config = {
                        display: display,
                        action: action,
                        displayPosition: DisplayPosition.TOP,
                        controlPosition: ControlPosition.TOP_RIGHT
                    };
                bus.fireEvent(new MapControlEvent(config));     
            }
        }
    );
    
    mol.ui.LayerControl.Layer = mol.ui.Display.extend(
        {
            init: function() {
                this._super(this._html());
            },

            getName: function() {
                var x = this._layerName,
                    s = '.layerNomial';
                return x ? x : (this._layerName = this.findChild(s));
            },  
            getSubName: function() {
                var x = this._layerSubName,
                    s = '.layerAuthor';
                return x ? x : (this._layerSubName = this.findChild(s));
            }, 
            getToggle: function() {
                var x = this._layerToggle,
                    s = '.toggle';
                return x ? x : (this._layerToggle = this.findChild(s));
            },  
            getType: function() {
                var x = this._layerType,
                    s = '.type';
                return x ? x : (this._layerType = this.findChild(s));
            },  
            getInfoLink: function() {
                var x = this._layerInfoLink,
                    s = '.info';
                return x ? x : (this._layerInfoLink = this.findChild(s));
            },  

            _html: function() {
                return  '<div class="layer widgetTheme">' +
                        '    <button><img class="type" src="/static/maps/search/points.png"></button>' +
                        '    <div class="layerName">' +
                        '        <div class="layerNomial">Smilisca puma</div>' +
                        '    </div>' +
                        '    <div class="buttonContainer">' +
                        '        <input class="toggle" type="checkbox">' +
                        '        <span class="customCheck"></span> ' +
                        '    </div>' +
                        '    <button class="info">i</button>' +
                        '</div>';
            }
        }
    );
    
    /**
     * The LayerControl display.
     */
    mol.ui.LayerControl.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super();
                this.setInnerHtml(this._html());
                this._config = config;
            },     
            getAddButton: function() {
                var x = this._addButton,
                    s = '.add';
                return x ? x : (this._addButton = this.findChild(s));
            },  
            getDeleteButton: function() {
                var x = this._deleteButton,
                    s = '.delete';
                return x ? x : (this._deleteButton = this.findChild(s));
            },

            getNewLayer: function(){
                var Layer = mol.ui.LayerControl.Layer,
                    r = new Layer();
                this.findChild('.mol-LayerControl-Layers').append(r);
                return r;
            },         
            _html: function(){
                return  '<div class="mol-LayerControl-Menu ">' +
                        '    <div class="label">Layers</div>' +
                        '    <div class="widgetTheme delete button">Delete</div>' +
                        '    <div class="widgetTheme add button">Add</div>' +
                        '</div>' +
                        '<div class="mol-LayerControl-Layers">' +
                        '</div>';
            }
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
     * Base class for map layers.
     */
    mol.ui.Map.MapLayer = Class.extend(
        {
            init: function(map, layer) {
                this._map = map;
                this._layer = layer;
                this._color = null;
            },
            
            // Abstract functions:
            show: function() {
                throw new mol.exceptions.NotImplementedError('show()');
            },
            hide: function() {
                throw new mol.exceptions.NotImplementedError('hide()');
            },
            isVisible: function() {                
                throw new mol.exceptions.NotImplementedError('isVisible()');
            },
            refresh: function() {
                throw new mol.exceptions.NotImplementedError('refresh()');
            },
            
            // Getters and setters:
            getLayer: function() {
                return this._layer;
            },
            getMap: function() {
                return this._map;           
            },
            getColor: function() {
                return this._color;
            },
            setColor: function(color) {
                this._color = color;
            }
        }
    );

    mol.ui.Map.PointLayer = mol.ui.Map.MapLayer.extend( 
        {
            init: function(map, layer, markerCanvas) {
                this._super(map, layer);
                this._markerCanvas = markerCanvas;
                this._points = null;
                this._icon = null;
                this._onMap = false;
                this._uncertaintySorter = {};
            },

            show: function() {
                var points = this._points,
                    map = this.getMap();

                if (!this.isVisible()) {
                    if (!points) {
                        this.refresh();
                    }
                    for (x in points) {
                        points[x].setMap(map);
                    }
                    this._onMap = true;
                }
            },

            hide: function() {
                var points = this._points;

                if (this.isVisible()) {
                    for (x in points) {
                        points[x].setMap(null);
                    }
                    this._onMap = false;
                }
            },

            isVisible: function() {                
                return this._onMap;
            },

            refresh: function() {
                var color = this.getColor(),
                    self = this;

                this._getPointIcon(
                    function(icon) {
                        self._icon = icon;
                        if (!self._points) {
                            self._createPoints();    
                        } else {
                            self._updateLayerColor();
                        }
                    }
                );  
            },

            _createPoints: function() {
                var layer = this.getLayer(),
                    lid = layer.getId(),
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
                this._points = [];
                for (p in data.records.publishers) {
                    resources = data.records.publishers[p].resources;
                    for (r in resources) {
                        occurrences = resources[r].occurrences;
                        for (o in occurrences) {
                            coordinate = occurrences[o].coordinates;
                            marker = this._createMarker(coordinate, iconUrl);
                            this._points.push(marker);
                                               
                            if (coordinate.coordinateUncertaintyInMeters != null) {
                                /*
                                 * A fairly raw way to deal with lots of uncertainty circles
                                 * overlapping each other. It just rounds the CUIM and the 
                                 * Coords and keeps a list of uniques, never recreating circles
                                 * of the samish size and samish place
                                 */
                                var cuim = parseFloat(coordinate.coordinateUncertaintyInMeters);
                                var approxCuim = Math.floor(cuim/100);
                                var approxCoord = Math.floor(coordinate.decimalLatitude * 100) + ":" + Math.floor(coordinate.decimalLongitude * 100)
                                var makeCircle = false;
                                if (!(approxCuim in this._uncertaintySorter)){
                                    this._uncertaintySorter[approxCuim] = {};
                                    this._uncertaintySorter[approxCuim][approxCoord] = marker;
                                    makeCircle = true;
                                } else if (!(approxCoord in this._uncertaintySorter[approxCuim])) {
                                    this._uncertaintySorter[approxCuim][approxCoord] = marker;
                                    makeCircle = true;
                                }
                                if (makeCircle) {
                                    this._points.push(this._createCircle(
                                                            marker.getPosition(),
                                                            cuim));
                                }
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

                var map = this.getMap(),
                    radius = parseFloat(coordinateUncertaintyInMeters),
                    opacity = 0.08,
                    circle = new google.maps.Circle(
                        {
                            map: map,
                            center: center,
                            clickable: false,
                            radius: radius,
                            fillColor: '#001d38',
                            strokeWeight: 0.7,                                
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
                var map = this.getMap(),
                    lat = parseFloat(coordinate.decimalLatitude),
                    lng = parseFloat(coordinate.decimalLongitude),
                    center = new google.maps.LatLng(lat, lng),
                    h = this._markerCanvas.getIconHeight(),
                    w = this._markerCanvas.getIconWidth(),
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
            
            _updateLayerColor: function() {
                var layer = this.getLayer(),
                    points = this._points,
                    urls = this._getIconUrls(),
                    markerCanvas = this._markerCanvas,
                    iconUrl = urls.iconUrl,
                    w = markerCanvas.getIconWidth(),
                    h = markerCanvas.getIconHeight(),
                    point = null,
                    MarkerImage = google.maps.MarkerImage,
                    Size = google.maps.Size,
                    Marker = google.maps.Marker,
                    image = new MarkerImage(iconUrl, new Size(w, h));
                
                for (x in points) {
                    point = points[x];
                    if (point instanceof Marker) {
                        point.setIcon(image);
                    }                        
                }
            },

            _getPointIcon: function(callback) {
                var icon = new Image(),
                    color = this.getColor(),
                    src = '/test/colorimage/placemark_default.png?'
                        + 'r=' + color.getRed() 
                        + '&g=' + color.getGreen() 
                        + '&b=' + color.getBlue();                

                icon.onload = function() {
                    callback(icon);
                };                

                icon.src = src;
            },
         
            _getIconUrls: function() {                
                var icon = this._icon,
                    markerCanvas = this._markerCanvas,
                    canvasSupport = markerCanvas.canvasSupport(),
                    icons = markerCanvas.getIcons(),
                    //background = icons.background,
                    //foreground = icons.foreground,
                    error = icons.error,
                    foreground = icons.foreground,
                    background = icons.background,
                    ctx = markerCanvas.getContext(),
                    w = markerCanvas.getIconWidth(),
                    h = markerCanvas.getIconHeight(),
                    url = null,
                    errorUrl = null;

                if (!canvasSupport) {
                    return {iconUrl: icon.src, iconErrorUrl: icon.src};
                }
                
                //ctx.drawImage(background, 0, 0, w, h);
                ctx.drawImage(background, 0, 0, w, h);
                ctx.drawImage(icon, 0, 0, w, h);
                ctx.drawImage(foreground, 0, 0, w, h);
                //ctx.drawImage(foreground, 0, 0, w, h);
                url = markerCanvas.getDataURL();
                ctx.drawImage(error, 0, 0, w, h);
                errorUrl = markerCanvas.getDataURL();

                return {iconUrl: url, iconErrorUrl: errorUrl};
            }
        }
    );

    mol.ui.Map.TileLayer = mol.ui.Map.MapLayer.extend(
        {
            init: function(map, layer) {
                this._super(map, layer);
                this._mapType = null;
                this._onMap = false;
            },
            
            // Abstract functions:
            _getTileUrlParams: function() {
                throw mol.exceptions.NotImplementedError('_getTileUrlParams()');
            },

            show: function() {
                if (!this.isVisible()) {
                    if (!this._mapType) {
                        this.refresh();
                    }
                    this.getMap().overlayMapTypes.push(this._mapType);
                    this._onMap = true;
                }
            },

            hide: function() {
                var keyName = this.getLayer().getKeyName(),
                    map = this.getMap();

                if (this.isVisible()) {
                    map.overlayMapTypes.forEach(
                        function(x, i) {
                            if (x && x.name === keyName) {
                                map.overlayMapTypes.removeAt(i);
                            }
                        }
                    );
                    this._onMap = false;
                }
            },
                        
            isVisible: function() {
                return this._onMap;
            },

            refresh: function() {              
                var self = this,
                    keyName = this.getLayer().getKeyName(),
                    layerSource = this.getLayer().getSource(),
                    color = this.getColor();

                this._mapType = new google.maps.ImageMapType(
                    {
                        getTileUrl: function(coord, zoom) {
                            var normalizedCoord = self._getNormalizedCoord(coord, zoom),
                                bound = Math.pow(2, zoom),
                                tileParams = '',
                                tileurl = null;                                

                            if (!normalizedCoord) {
                                return null;
                            }                    
                                                        
                            tileParams = tileParams + 'key_name=' + keyName;
                            tileParams = tileParams + '&source=' + layerSource;
                            tileParams = tileParams + '&r=' + color.getRed(),
                            tileParams = tileParams + '&g=' + color.getGreen(),
                            tileParams = tileParams + '&b=' + color.getBlue(),
                            tileParams = tileParams + '&x=' + normalizedCoord.x;
                            tileParams = tileParams + '&y=' + normalizedCoord.y;
                            tileParams = tileParams + '&z=' + zoom;
                            tileurl = "/data/tile?" + tileParams;

                            mol.log.info(tileurl);

                            return tileurl;
                        },
                        tileSize: new google.maps.Size(256, 256),
                        isPng: true,
                        opacity: 0.5,
                        name: keyName
                    });
            },

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
                this._controlDivs = {};
                this._mapLayers = {};
            },            

            _addMapLayer: function(map, layer) {
                var layerId = layer.getId(),
                    layerType = layer.getType(),
                    mapLayer = null;

                switch (layerType) {
                case 'points':
                    mapLayer = new mol.ui.Map.PointLayer(map, layer, this._markerCanvas);
                    break;
                case 'range':
                case 'ecoregion':
                case 'pa':
                    mapLayer = new mol.ui.Map.TileLayer(map, layer);
                    break;
                }
                this._mapLayers[layerId] = mapLayer;
            },

            _mapLayerExists: function(layerId) {
                return this._mapLayers[layerId] !== undefined;
            },
            
            _getMapLayer: function(layerId) {
                return this._mapLayers[layerId];
            },

            _removeMapLayer: function(layerId) {
                var mapLayer = this._getMapLayer(layerId);

                if (!mapLayer) {
                    return false;
                }

                mapLayer.hide();
                delete this._mapLayers[layerId];                
                return true;
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

                this._markerCanvas = new MarkerCanvas(28, 24);

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
                    map = this._map,
                    LayerEvent = mol.events.LayerEvent,
                    LayerControlEvent = mol.events.LayerControlEvent,
                    ColorEvent = mol.events.ColorEvent,
                    layers = this._layers,
                    self = this;
                
                bus.addHandler(
                    LayerControlEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            layerId = event.getLayerId();
                        if (action === 'delete-click') {                            
                            self._removeMapLayer(layerId);
                        }
                    }
                );

                bus.addHandler(
                    LayerEvent.TYPE,
                    function(event) {
                        var layer = event.getLayer(),
                            layerId = layer.getId(),     
                            mapLayer = self._getMapLayer(layerId),                        
                            action = event.getAction(),
                            colorEventConfig = {};
                                                
                        switch (action) {

                        case 'add':
                            if (mapLayer) {
                                return;
                            }                            
                            self._addMapLayer(map, layer);
                            colorEventConfig = {
                                action: 'get',
                                category: layer.getType(),
                                id: layerId
                            };
                            bus.fireEvent(new ColorEvent(colorEventConfig));
                            break;

                        case 'delete':
                            if (!mapLayer) {
                                return;
                            }    
                            self._removeMapLayer(layerId);
                            break;

                        case 'checked':
                            if (mapLayer) {
                                mapLayer.show();
                            }                                
                            break;                            

                        case 'unchecked':
                            if (mapLayer) {
                                mapLayer.hide();
                            }    
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
                            break;

                        case 'remove':
                            // TODO: Remove custom map control.
                            mol.log.todo('Remove custom map control');
                            break;                            
                        }
                    }
                );
            },

            _addColorEventHandler: function() {
                var ColorEvent = mol.events.ColorEvent,
                    bus = this._bus,
                    self = this;

                bus.addHandler(
                    ColorEvent.TYPE,
                    function(event) {
                        var color = event.getColor(),
                            category = event.getCategory(),
                            layerId = event.getId(),
                            mapLayer = self._getMapLayer(layerId),
                            action = event.getAction();

                        // Ignores event:
                        if (!mapLayer) {
                            return;
                        }

                        switch (action) {
                        case 'change':                        
                            mapLayer.setColor(color);
                            mapLayer.show();
                            break;
                        }                           
                    }
                );
            },
            
            _updateLayer: function(layer) {
                _updateLayerColor(layer);
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

                this._iconHeight = height;
                this._iconWidth = width;

                this._super('<canvas width=' + this._iconWidth + 
                            ' height=' + this._iconHeight + '>');

                this.setStyleName('mol-MarkerCanvas');

                this._ctx = this.getElement()[0].getContext("2d");

                this._iconLayers = {
                    background: new Image(),
                    foreground: new Image(),
                    error: new Image()
                };
                this._iconLayers.background.src = "/static/maps/placemarks/placemark-background.png";
                this._iconLayers.foreground.src = "/static/maps/placemarks/placemark-foreground.png";
                this._iconLayers.error.src = "/static/maps/placemarks/placemark-error.png";
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
 * Search module has a display used as a map control. It allows users to search
 * for layers to add to the map.
 */
MOL.modules.Search = function(mol) {
    
    mol.ui.Search = {};

    /**
     * Wraps a search response and surfaces an API for accessing data from it.
     */
    mol.ui.Search.Result = Class.extend(
        {
            init: function(response) {
                this._response = response;
            },

            /**
             * Gets layer names that satisfy a name, source, and type combined 
             * constraint. 
             *
             * @param name the layer name
             * @param source the layer source
             * @param type the layer type
             * @param profile the profile to test  
             * 
             */
            getLayers: function(name, source, type, profile) {
                var response = this._response,
                    currentProfile = profile ? profile : 'nameProfile',
                    nameProfile = name ? response.names[name] : null,
                    sourceProfile = source ? response.sources[source] : null,
                    typeProfile = type ? response.types[type] : null,
                    profileSatisfied = false;
                
                if (!name && !type && !source){
                    var keys = new Array();
                    for (i in response.layers) {
                        keys.push(i);
                    };
                    return keys;
                }
                
                switch (currentProfile) {
                    
                case 'nameProfile':
                    if (!name) {
                        return this.getLayers(name, source, type, 'sourceProfile');
                    }

                    if (nameProfile) {                                                
                        if (!source && !type) {
                            return nameProfile.layers;
                        }                         
                        if (source && type) {
                            if (this._exists(source, nameProfile.sources) &&
                                this._exists(type, nameProfile.types)) {
                                return _.intersect(
                                    nameProfile.layers, 
                                    this.getLayers(name, source, type, 'sourceProfile'));
                            }
                        } 
                        if (source && !type) {
                            mol.log.info('source no type');
                            if (this._exists(source, nameProfile.sources)) {
                                mol.log.info('return intersect(name.layers, sourceprofile');
                                return _.intersect(
                                   nameProfile.layers, 
                                   this.getLayers(name, source, type, 'sourceProfile'));
                            }
                        } 
                        if (!source && type) {
                            if (this._exists(type, nameProfile.types)) {
                                return _.intersect(
                                    nameProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));
                            }
                        }                            
                    } 
                    return [];                        
                    
                case 'sourceProfile':
                    if (!source) {
                        return this.getLayers(name, source, type, 'typeProfile');
                    }
                    
                    if (sourceProfile) {                        
                        if (!name && !type) {
                            return sourceProfile.layers;
                        }                         
                        if (name && type) {
                            if (this._exists(name, sourceProfile.names) &&
                                this._exists(type, sourceProfile.types)) {
                                return _.intersect(
                                    sourceProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));                                
                            }    
                        }                        
                        if (name && !type) {
                            if (this._exists(name, sourceProfile.names)) {
                                mol.log.info('returning source layers');
                                return sourceProfile.layers;
                            }
                        }                         
                        if (!name && type) {
                            if (this._exists(type, sourceProfile.types)) {
                                return _.intersect(
                                    sourceProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));                                
                            }
                        }                        
                    } 
                    return [];

                case 'typeProfile':
                    if (!type) {
                        return [];
                    }
                    
                    if (typeProfile) {
                        if (!name && !source) {
                            return typeProfile.layers;
                        }
                        if (name && source) {
                            if ( this._exists(name, typeProfile.names) &&
                                 this._exists(source, typeProfile.sources)) {
                                return typeProfile.layers;
                            }                            
                        }                         
                        if (name && !source) {
                            if (this._exists(name, typeProfile.names)) {
                                return typeProfile.layers;
                            }                            
                        }                         
                        if (!name && source) {
                            if (this._exists(source, typeProfile.sources)) {
                                return typeProfile.layers;
                            }                            
                        }                        
                    }                    
                    return [];
                } 
                return [];
            },

            getLayer: function(layer) {
                return this._response.layers[layer];
            },

            getKeys: function(id) {
                var res;
                switch(id.toLowerCase()){
                    case "types":
                        res = this._response.types;
                        break;
                    case "sources":
                        res = this._response.sources;
                        break;
                    case "names":
                        res = this._response.names;
                        break;
                    }
                return _.keys(res);   
            },
            
            getTypeKeys: function() {
                var x = this._typeKeys,
                    types = this._response.types;
                return x ? x : (this._typeKeys = _.keys(types));                
            },

            getType: function(type) {
                return this._response.types[type];
            },

            getSourceKeys: function() {
                var x = this._sourceKeys,
                    sources = this._response.sources;
                return x ? x : (this._sourceKeys = _.keys(sources));
            },
            
            getSource: function(source) {
                return this._response.sources[source];
            },
            
            getNameKeys: function() {
                var x = this._nameKeys,
                    names = this._response.names;
                return x ? x : (this._nameKeys = _.keys(names));
            },

            getName: function(name) {
                return this._response.names[name];
            },

            /**
             * Returns true if the name exists in the array, false otherwise.
             */
            _exists: function(name, array) {
                return _.indexOf(array, name) != -1;
            }
        }
    );

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
                this._nameFilter = null;
                this._sourceFilter = null;
                this._typeFilter = null;
                this._resultWidgets = [];
            },

            /**
             * Starts the engine by creating and binding the display.
             *
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                var text = {
                    select: 'Select',
                    selections: ['GBIF Species Points', 'MOL Species Range'],
                    go: 'Go',
                    search: 'Search',
                    info: 'more info',
                    next: 'Next Page',
                    add: 'Add'
                };
                this._bindDisplay(new mol.ui.Search.Display(), text);
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
            _bindDisplay: function(display, text) {                
                var widget = null,
                    result = null,
                    option = null,
                    optionsHtml = '',
                    self = this;

                this._display = display;
                display.setEngine(this);

                this._addLayerControlEventHandler();                

                display.hide();
                //display.getNextButton().hide();
                //display.getAddButton().hide();
                //display.getFiltersWidget().hide();
                display.getResultsContainer().hide();
                //display.getNavigationWidget().hide();

                // Go button
                widget = display.getGoButton();
                widget.text(text.go);
                widget.click(
                    function(event) {
                        self._onGoButtonClick();
                    }
                );

                widget = display.getSearchBox();
                
                widget.keyup(
                    function(event) {
                      if (event.keyCode === 13) {
                          self._onGoButtonClick();
                      }
                    }
                );

                // Add button:
                widget = display.getAddButton();
                widget.click(
                    function(event) {
                        self._onAddButtonClick();
                    }
                );
                
                // Close button:
                widget = display.getCloseButton();
                widget.click(
                    function(event) {
                        display.hide();
                        display.clearFilters();
                        display.clearResults();
                        display.getResultsContainer().hide();
                        //console.log('close');
                    }
                );
                  
                this._addDisplayToMap();
            },

            _onAddButtonClick: function() {
                var resultWidgets = this._resultWidgets || [],
                    rw = null,
                    result = null,
                    bus = this._bus,
                    api = this._api,
                    LayerAction = mol.ajax.LayerAction,
                    LayerEvent = mol.events.LayerEvent,
                    Layer = mol.model.Layer,
                    callback = null,
                    action = null,
                    display = this._display,
                    layer = null,
                    isChecked = false,
                    config = {
                        layer: layer
                    };

                mol.log.info('Handling add button click');
                display.getAddButton().attr('disabled', true);
                
                for (x in resultWidgets) {
                    result = resultWidgets[x];
                    rw = result.widget;
                    isChecked = rw.findChild('.checkbox').isChecked();
                    
                    if (!isChecked) {
                        continue;
                    }

                    switch (result.type) {
                    
                    case 'points':
                        action = new LayerAction('get-points', {layerName:result.name});
                        callback = this._layerActionCallback(result);
                        api.execute(action, callback);    
                        break;

                    case 'range':
                    case 'ecoregion':
                    case 'pa':
                        layer = new Layer(
                            {
                                type: result.type, 
                                source: result.source, 
                                name: result.name, 
                                name2: result.name2, 
                                key_name: result.key_name
                            } 
                        );
                        config.action = 'add';
                        config.layer = layer;
                        bus.fireEvent(new LayerEvent(config));                               
                        display.getAddButton().attr('disabled', false);                        
                        break;
                    }
                }
            },
            
            _layerActionCallback: function(result) {
                var LayerAction = mol.ajax.LayerAction,
                    ActionCallback = mol.ajax.ActionCallback,
                    LayerEvent = mol.events.LayerEvent,
                    Layer = mol.model.Layer,
                    layer = null,
                    bus = this._bus,
                    action = null,
                    config = {},
                    display = this._display;

                action = new LayerAction('get-points', {layerName:result.name});
                return new ActionCallback(
                    function(response) {
                        layer = new Layer(
                            {
                                type: result.type, 
                                source: result.source, 
                                name: result.name, 
                                name2: result.name2, 
                                key_name: result.key_name,
                                json: response
                            }
                        );
                        config.action = 'add';
                        config.layer = layer;
                        bus.fireEvent(new LayerEvent(config));                               
                        display.getAddButton().attr('disabled', false);
                    },
                    function(error) {
                        mol.log.error(error);
                    }
                );
            },

            _displayPage: function(layers) {
                var display = this._display,
                    fw = null,
                    res = null,
                    typeImg = null,
                    sourceImg = null,
                    resultWidgets = null;
                
                this._resultWidgets = [];
                resultWidgets = this._resultWidgets;
                display.clearResults();

                if (layers.length==0){
                    fw = display.noMatches();
                }

                for (r in layers){
                    res = layers[r];
                    fw = display.getNewResult();
                    typeImg = fw.getTypeImg();
                    sourceImg = fw.getSourceImg();

                    resultWidgets.push(
                        {
                            widget: fw, 
                            source: res.source, 
                            type: res.type, 
                            name: res.name,
                            name2: res.name2,
                            key_name: res.key_name
                        }
                    );

                    fw.getName().text(res.name);
                    fw.getAuthor().text(res.name2);
                    fw.getInfoLink().attr("attr","/static/dead_link.html");
                    sourceImg.attr("src","/static/maps/search/" + res.source.toLowerCase() + ".png");
                    sourceImg.click(function() {
                        mol.log.todo('Send source info to LeftBottom Modal');
                    });
                    typeImg.attr("src","/static/maps/search/" + res.type.toLowerCase() + ".png");
                    typeImg.click(function(){
                        mol.log.todo('Send type info to LeftBottom Modal');
                    });
                }

                display.getResultsContainer().show();
            },

            _allTypesCallback: function(filter, name) {
                var self = this;
                return function(event) {                    
                    var fo = filter.getOptions();
                    for (o in fo) {
                        fo[o].removeStyleName("selected");
                    }
                    new mol.ui.Element(event.target).addStyleName("selected");                    
                    self._processFilterValue(name, null);
                    };
            },

            _optionCallback: function(filter, name) {                
                var self = this;
                return function(event) {
                    var fo = filter.getOptions();
                    for (o in fo){
                        fo[o].removeStyleName("selected");
                    }
                    new mol.ui.Element(event.target).addStyleName("selected");                            
                    self._processFilterValue(name, new mol.ui.Element(event.target).text());
                }; 
            },
            
            _createNewFilter: function(name, data){
                var allTypes,
                    display = this._display,
                    filter = display.getNewFilter(),
                    keys = data[name.toLowerCase()],
                    self = this,
                    option = null,
                    tmpKeys = [],
                    k = null;

                filter.getFilterName().text(name);
                filter.attr('id', name);

                allTypes = filter.getNewOption();
                allTypes.text("All " + name);
                allTypes.addStyleName("all");
                allTypes.click(this._allTypesCallback(filter, name));
                allTypes.addStyleName("selected");
                for (k in keys) {
                    tmpKeys.push(k);
                }
                tmpKeys.sort();
                for (i in tmpKeys) {
                    k = tmpKeys[i];
                    option = filter.getNewOption();
                    option.text(k);
                    option.click(this._optionCallback(filter, name));
                }
            },

            _processFilterValue: function(key, value){
                var layers = new Array(),
                    self = this,
                    tmp = null;
                
                switch(key.toLowerCase()) {
                    case "names":
                        self._nameFilter = value;
                        break;
                    case "sources":
                        self._sourceFilter = value;
                        break;
                    case "types":
                        self._typeFilter= value;
                        break;
                    default:
                        break;
                }
          
                tmp = this._result.getLayers(
                    self._nameFilter,
                    self._sourceFilter,
                    self._typeFilter);

                for (v in tmp) {
                    layers.push(this._result.getLayer(tmp[v]));
                }
                
                this._displayPage(layers);
            },

            _onGoButtonClick: function() {
                var query = this._display.getSearchBox().val(),
                    LayerAction = mol.ajax.LayerAction,
                    action = new LayerAction('search', {query: query}),
                    ActionCallback = mol.ajax.ActionCallback,
                    api = this._api,
                    callback = null,
                    display = this._display,
                    self = this,
                    fn = null;
                
                callback = new ActionCallback(
                    function(response) {
                        var Result = mol.ui.Search.Result,
                            filterNames = ['Names','Sources','Types'];
                        self._result = new Result(response),
                        self._displayPage(response.layers);
                        display.clearFilters();
                        for (i in filterNames) {
                            fn = filterNames[i];
                            self._createNewFilter(fn,response);
                        }
                    },

                    function(error) {
                        mol.log.error(error);
                    }
                );

                api.execute(action, callback);
            },

            /**
             * Fires a MapControlEvent so that the display is attached to
             * the map as a control in the TOP_LEFT position.
             */
            _addDisplayToMap: function() {
                var MapControlEvent = mol.events.MapControlEvent,
                    display = this._display,
                    bus = this._bus,
                    DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    ControlPosition = mol.ui.Map.Control.ControlPosition,
                    action = 'add',
                    config = {
                        display: display,
                        action: action,
                        displayPosition: DisplayPosition.TOP,
                        controlPosition: ControlPosition.TOP_LEFT
                    };
                bus.fireEvent(new MapControlEvent(config));     
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
                            display.getSearchBox().focus();
                        }
                    }
                );
            }
        }
    );


    /**
     * A search result display.
     */
    mol.ui.Search.ResultWidget = mol.ui.Display.extend(
        {
            init: function() {
                this._super(this._html());
            },
            
            getCheckbox: function() {
                var x = this._checkbox,
                    s = '.checkbox';
                return x ? x : (this._checkbox = this.findChild(s));
            },
            
            getInfoLink: function() {
                var x = this._infoLink,
                    s = '.info';
                return x ? x : (this._infoLink = this.findChild(s));
            },
            
            getSourceButton: function() {
                var x = this._sourceButton,
                    s = '.source';
                return x ? x : (this._sourceButton = this.findChild(s));
            },
            
            getTypeButton: function() {
                var x = this._typeButton,
                    s = '.source';
                return x ? x : (this._typeButton = this.findChild(s));
            },
            
            getName: function() {
                var x = this._name,
                    s = '.resultNomial';
                return x ? x : (this._name = this.findChild(s));
            },
            getAuthor: function() {
                var x = this._author,
                    s = '.resultAuthor';
                return x ? x : (this._author = this.findChild(s));
            },
            getSourceImg: function() {
                var x = this._source,
                    s = '.source';
                return x ? x : (this._source = this.findChild(s));
            },
            getTypeImg: function() {
                var x = this._typeImg,
                    s = '.type';
                return x ? x : (this._typeImg = this.findChild(s));
            },

            _html: function() {
                return '<ul class="result">' + 
                       '        <div class="resultSource" ><button ><img class="source" src=""></button></div>' + 
                       '        <div class="resultType" ><button ><img class="type" src=""></button></div>' +
                       '        <div class="resultName">' + 
                       '            <div class="resultNomial" ></div>' + 
                       '            <div class="resultAuthor"></div>' + 
                       '        </div>' + 
                       '        <div class="resultLink"><a href="/static/dead_link.html" class="info">more info</a></div>' + 
                       '        <div class="buttonContainer"> ' + 
                       '            <input type="checkbox" class="checkbox" /> ' + 
                       '            <span class="customCheck"></span> ' + 
                       '        </div> ' + 
                       '    </ul>' + 
                       '<div class="break"></div>';
            }
        }
    );
                       
    /**
     * A search filter display
     */
    mol.ui.Search.FilterWidget = mol.ui.Display.extend(
        {
            init: function() {
                this._super(this._html());
                this._filterName = null;
                this._options = null;
            },

            getOptions: function() {
                if (!this._options){
                    this._options = this.findChild('.options');
                }
                return this._options.findChildren('.option');
            },
            
            getAllOption: function() {
                return this.findChild('.allOption');
            },

            getFilterName: function(n) {
                var s = '.filterName';
                if (!this._filterName){
                    this._filterName = this.findChild(s);
                }
                return this._filterName ;
                    
            },
            
            getNewOption: function() {
                if (!this._options){
                    this._options = this.findChild('.options');
                }
                var option = new mol.ui.Element();
                option.setStyleName('option');
                option.setInnerHtml(this._option());
                this._options.append(option);
                return option;
            },
            
            _option: function(){
                return '<div></div>';
            },
            
            _html: function() {
                return  '<div class="filter widgetTheme">' + 
                        '    <div class="filterName">Names</div>' + 
                        '    <div class="options"></div>' + 
                        '</div>';
            }
        }
    );

    /**
     * The search display.
     */
    mol.ui.Search.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super();
                this.setInnerHtml(this._html());
                this._config = config;
            },
            
            clearFilters: function() {
                _.each(
                    this.findChild('.filters').findChildren('.filter'),
                    function(element) {
                        element.remove();
                    }
                );
            },
            
            getFilters: function(id) {
                return this.findChild('#' + id);
            },
            
            getSearchWidget: function(){
                var x = this._searchWidget,
                    s = '.mol-LayerControl-Search';
                return x ? x : (this.searchWidget = this.findChild(s));
            },


            getResultsContainer: function(){
                var x = this._resultsContainer,
                    s = '.mol-LayerControl-Results';
                return x ? x : (this._resultsContainer = this.findChild(s));
            },


            getCloseButton: function(){
                var x = this._closeButton,
                    s = '.cancel';
                return x ? x : (this._closeButton = this.findChild(s));
            },

            getSearchBox: function(){
                var x = this._searchBox,
                    s = '.value';
                return x ? x : (this._searchBox = this.findChild(s));
            }, 
                        
            getGoButton: function() {
                var x = this._goButton,
                    s = '.execute';
                return x ? x : (this._goButton = this.findChild(s));
            },
            
            getNextButton: function() {
                var x = this._nextButton,
                    s = '.nextPage';
                return x ? x : (this._nextButton = this.findChild(s));
            },

            getAddButton: function(){
                var x = this._addButton,
                    s = '.addAll';
                return x ? x : (this._addButton = this.findChild(s));
            },
            
            clearResults: function(){
                this.findChild('.resultList').setInnerHtml("");
            },
            
            clearFilters: function(){
                this.findChild('.filters').setInnerHtml("");
            },
            
            getNewResult: function(){
                var ResultWidget = mol.ui.Search.ResultWidget,
                    r = new ResultWidget();
                this.findChild('.resultList').append(r);
                return r;
            },
            noMatches: function(){
                var r = new mol.ui.Element('<ul class="result">' + 
                                           '    <i>No matches</a>' + 
                                           '</ul>') ;
                this.findChild('.resultList').append(r);
                return r;
            },
            
            getNewFilter: function(){
                var FilterWidget = mol.ui.Search.FilterWidget,
                    r = new FilterWidget();
                this.findChild('.filters').append(r);
                return r;
            },

            _html: function(){
                return '<div class="mol-LayerControl-Search widgetTheme">' + 
                       '  <div class="title">Search:</div>' + 
                       '  <input class="value" type="text">' + 
                       '  <button class="execute">Go</button>' + 
                       '  <button class="cancel"><img src="/static/cancel.png" ></button>' + 
                       '</div>' + 
                       '<div class="mol-LayerControl-Results">' + 
                       '  <div class="filters">' + 
                       '  </div>' + 
                       '  <div class="searchResults widgetTheme">' + 
                       '    <div class="resultHeader">Results</div>' + 
                       '    <ol class="resultList"></ol>' + 
                       '    <div class="pageNavigation">' + 
                       '       <button class="addAll">Map Selected Layers</button>' + 
                       '    </div>' + 
                       '  </div>' + 
                       '</div>';
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
MOL.modules.Metadata = function(mol) { 
    
    mol.ui.Metadata = {};
    /**
     * Base class for map layers.
     */
    mol.ui.Metadata.Dataset = Class.extend(
        {
            init: function(dataset) {
                this._dataset = dataset;
            },
            // Getters and setters:
            getDataset: function() {
                return this._dataset;
            }
        }
    );
    /**
     * The Map Engine.
     */
    mol.ui.Metadata.Engine = mol.ui.Engine.extend(
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
            },            

            _addDataset: function(dataset) {
                var datasetId = dataset.getId(),
                    datasetType = dataset.getType();
                mol.log.todo('Metadata._addDataset');
                molDataset = new mol.ui.Metadata.Dataset(dataset);
                this._molDatasets[datasetId] = mapDataset;
            },

            _datasetExists: function(datasetId) {
                return this._molDatasets[datasetId] !== undefined;
            },
            
            _getDataset: function(datasetId) {
                return this._molDatasets[datasetId];
            },

            _removeDataset: function(datasetId) {
                var dataset = this._getDataset(datasetId);

                if (!dataset) {
                    return false;
                }
                delete this._molDatasets[datasetId];                
                return true;
            },
            
            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                this._bindDisplay(new mol.ui.Metadata.Display());
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display, text) {  
                var self = this,
                    bus = this._bus;
                    
                this._display = display;
                display.setEngine(this);   
                
                this._bus.bind(
                    mol.events.LayerEvent.TYPE,
                    function(event) {
                        var layer = event.getLayer();
                        var keyname = layer.getKeyName();
                        var datasetUi = self._display.addDataset(layer, keyname);
                    }
                );
                
            }
        }
    );

    /**
     * The LayerWidget.
     */
    mol.ui.Metadata.DatasetUI = mol.ui.Display.extend(
        {
            init: function(layer, keyname) {
                this._super('<div>');
                this.setStyleName(keyname);
                this.setInnerHtml("Metadata for: "+keyname);
            }
        }
    );
    /**
     * The Metadata Display <div> in the <body> element.
     */
    mol.ui.Metadata.Display = mol.ui.Display.extend(
        {

            /**
             * Constructs a new Metadata Display.
             * 
             * @param config the display configuration
             * @constructor
             */
            init: function(config) {
                this._id = 'metadata';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
                this._datasets = {};
            },
            
            addDataset: function(layer, keyname) {                
                var layerWidget = null;
                if (this._datasets[keyname]) {
                    return;
                }
                this._datasets[keyname] = null;
                //TODO: hit metadata api with keyname
                this.append(new mol.ui.Metadata.DatasetUI(layer,keyname));                
            },       
        }
    );
};
