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

mol.activity.LayersActivity.prototype.go = function(place) {
    // NOOP
};