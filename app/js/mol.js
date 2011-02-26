var MOL = MOL || {};    

$(function() {
    
    // Changes Underscore.js settings to perform Mustache.js style templating:
    _.templateSettings = {
        interpolate : /\{\{(.+?)\}\}/g
    };
 
    /**
     * Search view. Dispatches browser events to activity. 
     */
    MOL.SearchView = Backbone.View.extend({
        el: $('#SearchView'),        

        events: {
            "keyup #searchBox": "searchBoxKeyUp",
            "click #searchButton": "searchButtonClick"
        },

        // Initializes the view:
        initialize: function() {
            this.box = $('#searchBox');
            this.button = $('#searchButton');
        },
        
        // Returns the text in the #searchBox:
        getSearchText: function() {
            return this.box.val() || this.box.attr('placeholder');
        },
        
        // Handles keyup event on the #searchBox and dispatches to activity.
        searchBoxKeyUp: function(evt) {
            this.activity.searchBoxKeyUp(evt);
        },

        // Handles click event on the #searchButton and dispatches to activity.
        searchButtonClick: function(evt) {
            this.activity.searchButtonClick(evt);
        },

        // Sets the activity:
        setActivity: function(activity) {
            this.activity = activity;
        },

        // Sets the #searchBox text:
        setSearchText: function(t) {            
            this.box.val(t.split('=')[1]);
        }
    });

    /**
     * Search activity.
     */
    MOL.SearchActivity = function(view) {
        if (!(this instanceof MOL.SearchActivity)) {
            return new MOL.SearchActivity(view);
        }
        this.view = view;
        this.view.setActivity(this);

        // Goes to the place by updating the view:
        this.go = function(place) {
            var q = place.q;
            this.view.setSearchText(q);
        }
        
        // Clicks the search button if the enter key was pressed:
        this.searchBoxKeyUp = function(evt) {
            if (evt.keyCode === 13) {
                this.searchButtonClick(evt);
            }
        }
        
        // Saves a location and submits query to the server:
        this.searchButtonClick = function(evt) {
            var q = this.view.getSearchText();           
            var onSuccess = function(json) {
                alert('Success: ' + json);
            }
            var onFailure = function(error) {
                alert('Failure: ' + error);
            }
            var cb = new MOL.AsyncCallback(onSuccess, onFailure);
            MOL.rpc.execute('search', cb);
            MOL.controller.saveLocation('q=' + q);
        }
    };
       
    /**
     * The controller.
     */
    MOL.Controller = function() {
        var controller = Backbone.Controller.extend({
            initialize: function() {
                var view = new MOL.SearchView();
                this.searchActivity = new MOL.SearchActivity(view);
            },

            routes: {
                ":query": "search"
            },
        
            // Handles the search request route:
            search: function(query) {
                this.searchActivity.go({q:query});
            }
        });
        return new controller();
    };
        
    /**
     * Asynchronous callback that handles success and failure callbacks.
     */
    MOL.AsyncCallback = function(onSuccess, onFailure) {
        if (!(this instanceof MOL.AsyncCallback)) {
            return new MOL.AsyncCallback(onSuccess, onFailure);
        }
        this.onSuccess = onSuccess;
        this.onFailure = onFailure;
    };


    /**
     * RPC proxy.
     */
    MOL.RpcProxy = function() {
        if (!(this instanceof MOL.RpcProxy)) {
            return new MOL.RpcProxy();
        }
        this.execute = function(action, asyncCallback) {
            alert(action);
            asyncCallback.onSuccess('Yay!');
        }
    };
    
    
    /**
     * Event bus.
     */
    MOL.EventBus = function() {
        if (!(this instanceof MOL.EventBus)) {
            return new MOL.EventBus();
        }
        _.extend(this, Backbone.Events);
    };

    // Starts the app:
    MOL.rpc = new MOL.RpcProxy();
    MOL.bus = new MOL.EventBus();
    MOL.controller = new MOL.Controller();
    Backbone.history.start();
});
