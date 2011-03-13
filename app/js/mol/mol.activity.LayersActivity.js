/**
 * The layers widget activity.
 * 
 * @constructor
 */
mol.activity.LayersActivity = function(view) {
    if (!(this instanceof mol.activity.LayersActivity)) {
        return new mol.activity.LayersActivity(view);
    }
    this.view = view;
    this.view.setActivity(this);
    return this;
};

mol.activity.LayersActivity.prototype.addLayerClick = function(evt) {
    this.view.showAddLayerDialog(true);  
};

mol.activity.LayersActivity.prototype.handleAddPoints = function (source, type, value, id) {
    var self = this,
        cb = null,
        speciesKey = "animalia/species/" + value.replace(' ', '_').toLowerCase();
    if (source=== 'GBIF' && type === 'points') {
        cb = new mol.api.AsyncCallback(
            function(json) { // Success
                mol.eventBus.trigger('gbif-points-event', json, id);
                self.view.doneLoading(id);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        params = {speciesKey: speciesKey};
        mol.apiProxy.execute({action: 'points', params: params}, cb);
    }    
};

mol.activity.LayersActivity.prototype.go = function(place) {
    var speciesKey = place.params.speciesKey,
        layerId = speciesKey.replace('/', '_'),
        layerSource = 'GBIF',
        layerName = speciesKey.split('/')[2].replace('_', ' '),
        self = this,
        pointCb = new mol.api.AsyncCallback(
            function(json) { // Success
                mol.eventBus.trigger('gbif-points-event', json, layerId);
                self.view.addLayerControl(layerId, layerSource, layerName);
                self.view.doneLoading(layerId);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        metaCb = new mol.api.AsyncCallback(
            function(json) { // Success
                mol.eventBus.trigger('rangemap-metadata-event', json, layerId);
                self.view.addLayerControl(layerId, 'MOL', layerName);
                self.view.doneLoading(layerId);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        params = {speciesKey: speciesKey};
    mol.apiProxy.execute({action: 'points', params: params}, pointCb);    
    mol.apiProxy.execute({action: 'rangemap_metadata', params: params}, metaCb); 
};
