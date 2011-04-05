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
                    widget = null;


                this._display = display;
                display.setEngine(this);            
                
                // Restart button:
                widget = display.getAddButton();
                widget.click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('add-click'));
                    }
                );
                
                this._addDisplayToMap();
                
                bus.addHandler(
                    LayerEvent.TYPE, 
                    function(event) {
                        var action = event.getAction(),
                            layer = event.getLayer(),
                            layerUi = null,
                            display = self._display;
                    
                        switch (action) {

                        case 'add':
                            // widget = display.addControl();
                            // TODO: set widget props/callbacks
                            mol.log.info('Adding layer control to right controller');
                            layerUi = display.getNewLayer();
                            layerUi.getName().text(layer.name);
                            layerUi.getAuthor().text(layer.name2);
                            layerUi.getSource().attr("src","/static/maps/search/"+ layer.source +".png");
                            mol.log.info('Adding layer control to right controller');
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
            getAuthor: function() {
                var x = this._layerAuthor,
                    s = '.layerAuthor';
                return x ? x : (this._layerAuthor = this.findChild(s));
            }, 
            getToggle: function() {
                var x = this._layerToggle,
                    s = '.toggle';
                return x ? x : (this._layerToggle = this.findChild(s));
            },  
            getSource: function() {
                var x = this._layerSource,
                    s = '.source';
                return x ? x : (this._layerSource = this.findChild(s));
            },  
            getInfoLink: function() {
                var x = this._layerInfoLink,
                    s = '.info';
                return x ? x : (this._layerInfoLink = this.findChild(s));
            },  

            _html: function() {
                return  '<div id="points_GBIF_Puma_concolor" class="layer widgetTheme">' +
                        '    <div class="layerToggle">' +
                        '        <input type="radio" name="active-layer">' +
                        '    </div>' +
                        '    <div class="layerName">' +
                        '        <div class="layerNomial">Smilisca puma</div>' +
                        '        <div class="layerAuthor">A. Steele</div>' +
                        '    </div>' +
                        '    <input class="toggle" type="checkbox">' +
                        '    <button class="source"><img class="source" src=""></button>' +
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
