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

