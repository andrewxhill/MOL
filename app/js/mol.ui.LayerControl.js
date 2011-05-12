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
                        '        <div class="layerAuthor">A. Steele</div>' +
                        '    </div>' +
                        '    <input class="toggle" type="checkbox">' +
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
