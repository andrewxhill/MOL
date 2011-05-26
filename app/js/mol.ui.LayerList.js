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
                this._layerIds = [];
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
