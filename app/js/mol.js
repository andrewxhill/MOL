var MOL = MOL || {};    

$(function() {
    
    // Changes Underscore.js settings to perform Mustache.js style templating:
    _.templateSettings = {
        interpolate : /\{\{(.+?)\}\}/g
    };
 
    /**
     * Search view.
     */
    MOL.SearchWidget = Backbone.View.extend({
        el: $('#SearchWidget'),        

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
        
        // Handles keyup event on the #searchBox and dispatches to presenter.
        searchBoxKeyUp: function(evt) {
            this.presenter.searchBoxKeyUp(evt);
        },

        // Handles click event on the #searchButton and dispatches to presenter.
        searchButtonClick: function(evt) {
            this.presenter.searchButtonClick(evt);
        },

        // Sets the presenter:
        setPresenter: function(presenter) {
            this.presenter = presenter;
        },

        // Sets the #searchBox text:
        setSearchText: function(t) {            
            this.box.val(t.split('=')[1]);
        }
    });

    /**
     * Search presenter.
     */
    MOL.SearchPresenter = Backbone.Model.extend({
        // Goes to the place by updating the view:
        go: function(place) {
            var q = place.q;
            this.view.setSearchText(q);
        },
        
        // Clicks the search button if the enter key was pressed:
        searchBoxKeyUp: function(evt) {
            if (evt.keyCode === 13) {
                this.searchButtonClick();
            }
        },
        
        // Saves a location and submits query to the server:
        searchButtonClick: function() {
            var q = this.view.getSearchText();
            MOL.Controller.saveLocation('q=' + q);
        },

        // Sets the view:
        setView: function(view) {
            this.view  = view;
        }
    });
       
    /**
     * The controller.
     */
    MOL.AppController = Backbone.Controller.extend({
        routes: {
          ":query": "search"
        },
        
        // Sets up the views and presenters:
        initialize: function() {
            var view = new MOL.SearchWidget();
            this.searchPresenter = new MOL.SearchPresenter();
            this.searchPresenter.setView(view);
            view.setPresenter(this.searchPresenter);
        },
        
        // Handles the search request route:
        search: function(query) {
            this.searchPresenter.go({q:query});
        }
      });

    // Starts the app:
    MOL.Controller = new MOL.AppController();
    Backbone.history.start();
});
