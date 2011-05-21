/**
 * Copyright 2011 Andrew W. Hill, Aaron Steele
 * 
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

                this._addLocationHandler();

                this._colorSetter = new mol.ui.ColorSetter.Api({'bus': this._bus});
                this._container = $('body');

                this._mapEngine = new mol.ui.Map.Engine(this._api, this._bus);
                this._mapEngine.start(this._container);

                this._layerControlEngine = new mol.ui.LayerControl.Engine(this._api, this._bus);
                this._layerControlEngine.start(this._container);                

                this._searchEngine = new mol.ui.Search.Engine(this._api, this._bus);
                this._searchEngine.start(this._container);
                
                this._metadataEngine = new mol.ui.Metadata.Engine(this._api, this._bus);
                this._metadataEngine.start(this._container);
            },
            
            _addLocationHandler: function() {
                var bus = this._bus,
                    LocationEvent = mol.events.LocationEvent,
                    self = this;
                
                bus.addHandler(
                    LocationEvent.TYPE,
                    function(event) {
                        var mapState = '',
                            searchState = '',
                            url = window.location.href,
                            action = event.getAction(),
                            mapEngine = self._mapEngine,
                            searchEngine = self._searchEngine;

                        switch (action) {
                        case 'get-url':
                            mapState = mol.util.urlEncode(mapEngine.getPlaceState());
                            searchState = mol.util.urlEncode(searchEngine.getPlaceState());
                            url = url + mapState + '&' + searchState;
                            bus.fireEvent(LocationEvent({url: url}, 'take-url'));
                            break;
                        }
                    }
                );
                
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
