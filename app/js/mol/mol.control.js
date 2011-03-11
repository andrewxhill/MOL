/**
 * The controller for handling routing and history.
 * 
 * @constructor
 */
mol.control.Controller = function() {
    var controller = Backbone.Controller.extend(
        {
            initialize: function() {
                var searchView = new mol.view.SearchView();
                this.searchActivity = new mol.activity.SearchActivity(searchView);                
            },

            routes: {
                ":query": "search"
            },
            
            // Handles the search request route:
            search: function(query) {
                this.searchActivity.go({params: mol.util.parseQuery(query)});                    
            }
        });
    return new controller();
};

/**
 * The controller for handling routing and history.
 * 
 * @constructor
 */
mol.control.RangeMapController = function() {
    var controller = Backbone.Controller.extend(
        {
            initialize: function() {
                this.activities = [];
                var rangeMapView = new mol.view.RangeMapView();                    
                this.activities.push(new mol.activity.RangeMapActivity(rangeMapView));
                var layersView = new mol.view.LayersView();
                this.activities.push(new mol.activity.LayersActivity(layersView));
            },
            
            routes: {
                ":query": "rangeMap"
            },
            
            speciesKeyFromUrl: function () {
                var pathArray = window.location.pathname.split( '/' );
                return pathArray[2] + "/" + pathArray[3] + "/" + pathArray[4];
            },

            rangeMap: function(query) {
                var params = mol.util.parseQuery(query);
                params.speciesKey = this.speciesKeyFromUrl();
                for (a in this.activities) {
                    var activity = this.activities[a];
                    activity.go({params: params});
                }                
            }
        });
    return new controller();
};
