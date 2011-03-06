var mol = mol || {};    

mol.init = function() {
        
    // Function for building namespaces:
    mol.ns = function(namespace) {
        var parts = namespace.split('.');
        var parent = mol;
        var i;
        if (parts[0] === 'mol') {
            parts = parts.slice(1);
        }
        for (i = 0; i < parts.length; i += 1) {
            if (typeof parent[parts[i]] === 'undefined') {
                parent[parts[i]] = {};
            }
            parent = parent[parts[i]];
        }
        return parent;
    };
    
    // Creates MOL specific namespaces:
    mol.ns('mol.util');
    mol.ns('mol.activity');
    mol.ns('mol.view');

    // Serializes an object into a URL encoded GET query string.
    mol.util.serialize = function(obj) {
        var str = [];
        for(var p in obj)
            str.push(p + "=" + encodeURIComponent(obj[p]));
        return str.join("&");
    };

    mol.util.getUrlQueryParams = function(query) {
        var e,
            a = /\+/g,  
            r = /([^&=]+)=?([^&]*)/g,
            d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
            q = query.replace('#', '').replace('?', '');
        var urlParams = {};
        while ((e = r.exec(q))) {
            urlParams[d(e[1])] = d(e[2]);
        }
        return urlParams;
    };
    
    // Changes Underscore.js settings to perform Mustache.js style templating:
    _.templateSettings = {
        interpolate : /\{\{(.+?)\}\}/g
    };
    
    mol.SpeciesModel = Backbone.Model.extend({});

    mol.SearchResults = Backbone.Collection.extend({
        model: mol.SpeciesModel,

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
    mol.view.SearchView = Backbone.View.extend({
        el: $('#SearchView'),        

        events: {
            "keyup #searchBox": "searchBoxKeyUp",
            "click #searchButton": "searchButtonClick"
        },

        // Initializes the view:
        initialize: function() {
            this.box = $('#searchBox');
            this.button = $('#searchButton');
            this.tableContainer = $('#searchTable')[0];
            this.table = new google.visualization.Table(this.tableContainer);
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
            this.box.val(t);
        }
    });

    /**
     * Search activity.
     */
    mol.activity.SearchActivity = function(view) {
        if (!(this instanceof mol.activity.SearchActivity)) {
            return new mol.activity.SearchActivity(view);
        }
        this.view = view;
        this.view.setActivity(this);
        this.pageSize = 2;
        this.limit = 2;
        this.offset = 0;
        this.currentDataTable = null;
        this.table = this.view.table;
        this.currentPageIndex = 0;

        // Wire the up callback for paging:
        var self = this;
        var addListener = google.visualization.events.addListener;
        addListener(this.view.table, 'page', function(e) {
            self.handlePage(e);
        });

        // Configure query options:
        this.tableOptions = {page: 'event', 
                             showRowNumber: true,
                             allowHtml: true, 
                             pagingButtonsConfiguration: 'both',
                             pageSize: this.pageSize};
        this.updatePagingState(0);
        return true;
    };

    /**
     * Updates the paging state.
     * 
     */
    mol.activity.SearchActivity.prototype.updatePagingState = function(pageIndex) {
        var pageSize = this.pageSize;
        
        if (pageIndex < 0) {
            return false;
        }
        var dataTable = this.currentDataTable;
        if ((pageIndex == this.currentPageIndex + 1) && dataTable) {
            if (dataTable.getNumberOfRows() <= pageSize) {
                return false;
            }
        }
        this.currentPageIndex = pageIndex;
        var newStartRow = this.currentPageIndex * pageSize;
        // Get the pageSize + 1 so that we can know when the last page is reached.
        //this.limit = pageSize + 1;
        this.offset = newStartRow;
        // Note: row numbers are 1-based yet dataTable rows are 0-based.
        this.tableOptions['firstRowNumber'] = newStartRow + 1;
        return true;
    };

    
    /**
     * Sends a query and draws the results.
     * 
     */
    mol.activity.SearchActivity.prototype.sendAndDraw = function(saveLoc) {
        var cb = new mol.AsyncCallback(this.onSuccess(), this.onFailure),
            params = this.getSearchParams(),
            historyState = this.getHistoryState();
        this.table.setSelection([]);
        mol.api.execute({action: 'search', params: params}, cb);
        if (saveLoc) {
            mol.controller.saveLocation(mol.util.serialize(historyState));            
        }
    };

    /**
     * Handles a paging request from the table.
     * 
     */
    mol.activity.SearchActivity.prototype.handlePage = function(properties) {
        var localTableNewPage = properties['page']; // 1, -1 or 0
        var newPage = 0;
        if (localTableNewPage != 0) {
            newPage = this.currentPageIndex + localTableNewPage;
        }
        if (this.updatePagingState(newPage)) {
            this.sendAndDraw(true);
        }
    };

    /**
     * Goes to a place (provided by controller) by updating the view.
     * 
     */
    mol.activity.SearchActivity.prototype.go = function(place) {
        var params = place.params,
            offset = params.offset;        
        this.offset = offset == null ? this.offset : Number(offset);
        this.limit = Number(params.limit) || this.limit;
        this.currentPageIndex = this.offset / this.pageSize;
        this.view.setSearchText(params.q);
        var newStartRow = this.currentPageIndex * this.pageSize;
        this.tableOptions['firstRowNumber'] = newStartRow + 1;
        this.sendAndDraw(false);            
    };
        
    // Clicks the search button if the enter key was pressed:
    mol.activity.SearchActivity.prototype.searchBoxKeyUp = function(evt) {
        if (evt.keyCode === 13) {
            this.searchButtonClick(evt);
        }
    };
    
    
    /**
     * Gets the search params for the request.
     */
    mol.activity.SearchActivity.prototype.getSearchParams = function() {
        return {q: this.view.getSearchText(),
                limit: this.limit + 1,
                offset: this.offset,
                tqx: true};
    };

    /**
     * Gets the search params for the request.
     */
    mol.activity.SearchActivity.prototype.getHistoryState = function() {
        return {q: this.view.getSearchText(),
                limit: this.limit,
                offset: this.offset,
                tqx: true};
    };
    
    mol.activity.SearchActivity.prototype.onSuccess = function() {
        var self = this;
        return function(json) {
            var data = null;
            self.currentDataTable = null;
            google.visualization.errors.removeAll(self.view.tableContainer);            
            eval("data = " + json);
            self.currentDataTable = new google.visualization.DataTable(data);
            self.table.draw(self.currentDataTable, self.tableOptions);
        };
    };
    
    mol.activity.SearchActivity.prototype.onFailure = function(error) {
        alert('Failure: ' + error);
    };
    
    // Saves a location and submits query to the server:
    mol.activity.SearchActivity.prototype.searchButtonClick = function(evt) {
        this.offset = 0;
        this.currentPageIndex = 0;
        this.sendAndDraw(true);
    };
       
    /**
     * The controller.
     */
    mol.Controller = function() {
        var controller = Backbone.Controller.extend({
            initialize: function() {
                var view = new mol.view.SearchView();
                this.searchActivity = new mol.activity.SearchActivity(view);
            },

            routes: {
                ":query": "search"
            },
        
            // Handles the search request route:
            search: function(query) {
                this.searchActivity.go({params: mol.util.getUrlQueryParams(query)});                    
            }
        });
        return new controller();
    };
        
    /**
     * Asynchronous callback that handles success and failure callbacks.
     */
    mol.AsyncCallback = function(onSuccess, onFailure) {
        if (!(this instanceof mol.AsyncCallback)) {
            return new mol.AsyncCallback(onSuccess, onFailure);
        }
        this.onSuccess = onSuccess;
        this.onFailure = onFailure;
    };


    /**
     * API proxy.
     */
    mol.ApiProxy = function() {
        if (!(this instanceof mol.ApiProxy)) {
            return new mol.ApiProxy();
        }
        this.execute = function(request, cb) {
            if (request.action === 'search') {
                var xhr = $.post('/api/taxonomy', request.params, 'json');
                xhr.success(cb.onSuccess);
                xhr.error(cb.onError);
            }
        };
    };
    
    
    /**
     * Event bus.
     * @constructor
     */
    mol.EventBus = function() {
        if (!(this instanceof mol.EventBus)) {
            return new mol.EventBus();
        }
        _.extend(this, Backbone.Events);
    };

    // Starts the app:
    mol.api = new mol.ApiProxy();
    mol.bus = new mol.EventBus();
    mol.controller = new mol.Controller();
    Backbone.history.start();
};
