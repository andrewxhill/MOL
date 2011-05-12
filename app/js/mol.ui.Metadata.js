
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
