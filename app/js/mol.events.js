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
     * Place event.
     */
    mol.events.LocationEvent = mol.events.Event.extend(
        {
            init: function(location, action, refresh) {
                this._super('LocationEvent', action);
                this._location = location;
                this._refresh = refresh;
            },

            getRefresh: function() {                
                return this._refresh;
            },

            getLocation: function() {
                return this._location;
            }
        }
    );
    mol.events.LocationEvent.TYPE = 'LocationEvent';

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
                this._zoomLayerIds = config.zoomLayerIds;
            },

            getLayer: function() {
                return this._layer;
            },


            getZoomLayerIds: function() {
                return this._zoomLayerIds;
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
            init: function(action, layerId, zoomLayerIds) {
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
