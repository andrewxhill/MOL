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

mol.activity.LayersActivity.prototype.handleDeleteLayer = function (layerId) {
    mol.eventBus.trigger('delete-layer-event', layerId);
};

mol.activity.LayersActivity.prototype.showLayer = function(layerId, isVisible, layerType) {
    mol.eventBus.trigger('hide-layer-event', layerId, isVisible, layerType);
};

mol.activity.LayersActivity.prototype.go = function(place) {
    var speciesKey = place.params.speciesKey,
        layerId = speciesKey.split('/').join('_'),
        layerSource = 'GBIF',
        layerName = speciesKey.split('/')[2].replace('_', ' '),
        self = this,
        pointCb = new mol.api.AsyncCallback(
            function(json) { // Success
                var id = "points_"+layerId;
                mol.eventBus.trigger('gbif-points-event', json, id);
                self.view.addLayerControl(id, layerSource, layerName);
                self.view.doneLoading(id);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        metaCb = new mol.api.AsyncCallback(
            function(json) { // Success
                var id = "range_"+layerId;
                mol.eventBus.trigger('rangemap-metadata-event', json, id);
                self.view.addLayerControl(id, 'MOL', layerName);
                self.view.doneLoading(id);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        params = {speciesKey: speciesKey};
    mol.apiProxy.execute({action: 'points', params: params}, pointCb);    
    mol.apiProxy.execute({action: 'rangemap_metadata', params: params}, metaCb); 
};
