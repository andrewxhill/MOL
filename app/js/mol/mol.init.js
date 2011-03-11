/**
 * Initializes the MOL app and should be called after the DOM is ready.
 */
mol.init = function() {        
    // Changes Underscore.js settings to use Mustache.js templating.
    // Note: Only grandpa does templating.
    _.templateSettings = {
        interpolate : /\{\{(.+?)\}\}/g
    };
    mol.apiProxy = mol.apiProxy || new mol.api.ApiProxy();
    mol.eventBus = mol.eventBus || new mol.event.EventBus();
    mol.controller = mol.controller || new mol.control.Controller();
    Backbone.history.start();
};

/**
 * Initializes the MOL app and should be called after the DOM is ready.
 */
mol.initRangeMap = function() {        
    mol.apiProxy = mol.apiProxy || new mol.api.ApiProxy();
    mol.eventBus = mol.eventBus || new mol.event.EventBus();
    mol.controller = new mol.control.RangeMapController();
    Backbone.history.start();
};
