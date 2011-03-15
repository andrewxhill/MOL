/**
 * Initializes the MOL app and should be called after the DOM is ready.
 */
mol.initRangeMap = function(context) {        
    mol.apiProxy = mol.apiProxy || new mol.api.ApiProxy();
    mol.eventBus = mol.eventBus || new mol.event.EventBus();
    mol.context = context;
    mol.rangeMap = new mol.maps.Map($(context));
    mol.layerStack = new mol.ui.LayerStack(context);
    //Backbone.history.start();
};
