
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
    console.log('metadata hit');
    /**
     * Base class for map layers.
     */
    mol.ui.Metadata.Dataset = Class.extend(
        {
            init: function(dataset) {
                this._dataset = dataset;
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
                this._bindDisplay(new mol.ui.Metadata.Display(), container);
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             * @override mol.ui.Engine.go
             */

            _bindDisplay: function(display, container) {
                this._display = display;
                display.setEngine(this);                

                container.append(display.getElement());
            },

            /**
             * Adds an event handler for new layers.
             */
            _addLayerEventHandler: function() {
                var bus = this._bus,
                    LayerEvent = mol.events.LayerEvent,
                    LayerControlEvent = mol.events.LayerControlEvent,
                    layers = this._layers,
                    self = this;
                
                bus.addHandler(
                    LayerControlEvent.TYPE,
                    function(event) {
                        var dataset = event.getLayer(),
                            datasetId = layer.getId(),     
                            dataset = self._getDataset(datasetId),                        
                            action = event.getAction();
                                                
                        switch (action) {

                        case 'add':
                            if (dataset) {
                                return;
                            }                            
                            self._addDataset(dataset);
                            break;

                        case 'delete':
                            if (!datasetId) {
                                return;
                            }    
                            self._removeDatasetId(datasetId);
                            break;
                        }
                    }
                );
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
                console.log('metadata display init');
                this._id = 'metadata';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
            }        
        }
    );
};
