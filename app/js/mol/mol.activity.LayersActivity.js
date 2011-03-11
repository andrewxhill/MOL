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
        speciesKey = "animalia/species/" + value.replace(' ', '_');
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
    // NOOP
};