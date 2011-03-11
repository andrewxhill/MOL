/**
 * The range map activity.
 * 
 * @constructor
 */
mol.activity.RangeMapActivity = function(view) {
    if (!(this instanceof mol.activity.RangeMapActivity)) {
        return new mol.activity.RangeMapActivity(view);
    }
    var self = this;
    this.view = view;
    mol.eventBus.bind('gbif-points-event', 
                      function(json) {
                          self.view.renderPoints(json); 
                      });                     
    return this;
};

/**
 * Goes to a place that is provided by the controller.
 * 
 * @param place The place object to go to
 */
mol.activity.RangeMapActivity.prototype.go = function(place) {
    var speciesKey = place.params.speciesKey,
        self = this,
        cb = new mol.api.AsyncCallback(
            function(json) { // Success
                self.view.initMetadata(json);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        pointsCb = new mol.api.AsyncCallback(
            function(json) { // Success
                self.view.renderPoints(json);
            },
            function(error) { // Failure
                alert('Error: ' + error);            
            }),
        params = {speciesKey: speciesKey};
    mol.apiProxy.execute({action: 'rangemap', params: params}, cb);
    mol.apiProxy.execute({action: 'points', params: params}, pointsCb);
};
