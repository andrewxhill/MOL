var MOL = MOL || {};    

$(function() {
    
    // Builds a namespace.
    MOL.ns = function(namespace) {
        var parts = namespace.split('.');
        var parent = MOL;
        var i;
        if (parts[0] === 'MOL') {
            parts = parts.slice(1);
        }
        for (i = 0; i < parts.length; i += 1) {
            if (typeof parent[parts[i]] === 'undefined') {
                parent[parts[i]] = {};
            }
            parent = parent[parts[i]];
        }
        return parent;
    }
    
    MOL.ns('MOL.util');

    // Serializes an object into a GET query string.
    MOL.util.serialize = function(obj) {
        var str = [];
        for(var p in obj)
            str.push(p + "=" + encodeURIComponent(obj[p]));
        return str.join("&");
    }
    
    // Changes Underscore.js settings to perform Mustache.js style templating:
    _.templateSettings = {
        interpolate : /\{\{(.+?)\}\}/g
    };
    
    MOL.SpeciesModel = Backbone.Model.extend({});

    MOL.SearchResults = Backbone.Collection.extend({
        model: MOL.SpeciesModel,

        url: function() {
            return '/api/taxonomy?' + this.query;
        },

        setQuery: function(query) {
            this.query = query;
        }
    });
    

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
            this.results = $('#searchResults');
        },
        
        // Returns the text in the #searchBox:
        getSearchText: function() {
            return this.box.val() || this.box.attr('placeholder');
        },
        
        renderResults: function(json) {
            var template = $('#foo').html();
            var html = Mustache.to_html(template, json).replace(/^\s*/mg, '');
            $('#searchResults').html(html);
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
        this.pageSize = 10;
        this.limit = this.pageSize + 1;
        this.offset = 0;

        // Goes to the place by updating the view:
        this.go = function(place) {
            var q = place.q;
            this.view.setSearchText(q);
        };
        
        // Clicks the search button if the enter key was pressed:
        this.searchBoxKeyUp = function(evt) {
            if (evt.keyCode === 13) {
                this.searchButtonClick(evt);
            }
        };

        this.getSearchParams = function() {
            return {q: this.view.getSearchText(),
                    limit: this.limit,
                    offset: this.offset};
        };
        
        this.onSuccess = function() {
            var self = this;
            return function(json) {
                alert('Success: ' + JSON.stringify(json));
                self.view.renderResults(json);
            }
        };

        this.onFailure = function(error) {
            alert('Failure: ' + error);
        }

        // Saves a location and submits query to the server:
        this.searchButtonClick = function(evt) {
            var cb = new MOL.AsyncCallback(this.onSuccess(), this.onFailure);            
            var params = null;
            this.offset = 0;
            params = this.getSearchParams();
            MOL.api.execute({action: 'search', params: params}, cb);
            MOL.controller.saveLocation(MOL.util.serialize(params));
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
     * API proxy.
     */
    MOL.ApiProxy = function() {
        if (!(this instanceof MOL.ApiProxy)) {
            return new MOL.ApiProxy();
        }
        this.execute = function(request, cb) {
            if (request.action === 'search') {
                var xhr = $.post('/api/taxonomy', request.params, 'json');
                xhr.success(cb.onSuccess);
                xhr.error(cb.onError);
            }
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
    MOL.api = new MOL.ApiProxy();
    MOL.bus = new MOL.EventBus();
    MOL.controller = new MOL.Controller();
    Backbone.history.start();
});
