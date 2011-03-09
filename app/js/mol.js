/* 
 * Copyright (c) 2011 Map of Life 
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @fileoverview This file contains MOL specific app code. It depends on 
 * backbone.js, JQuery, json2.js, underscore.js, and mustache.js libraries.
 * It generally follows the Model-View-Presenter architecture via backbone.js
 * support for models, views, controllers, and browser history support. All
 * presenters are named "Activity".
 * 
 * @author eightysteele@gmail.com (Aaron Steele) 
 * @author andrewxhill@gmail.com (Andrew Hill)
 */

// The global MOL namespace that encapsulates all the sweet stuff:
var mol = mol || {};    

/**
 * Helper for building namespaces.
 * 
 * @param namespace The namespace to build within mol global namespace
 */
mol.ns = function(namespace) {
    var parts = namespace.split('.'),
        parent = mol;
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

// =============================================================================
// mol.util

mol.ns('mol.util');

/**
 * Helper that returns a boolean based on a string. Returns true if string is
 * 'true', returns false if string is 'false', otherwise returns false.
 * 
 * @param s The s to test 
 */
mol.util.isBool = function (s) {
    return (/^true$/i).test(s);
};

/**
 * Helper that serializes an object into a URL encoded GET query string.
 * 
 * @param obj The object to serialize
 */
mol.util.serializeQuery = function(obj) {
    var str = [];
    for(var p in obj)
        str.push(p + "=" + encodeURIComponent(obj[p]));
    return str.join("&");
};

/**
 * Helper that parses a URL encoded GET query string into an object.
 * 
 * @param query The query string
 */
mol.util.parseQuery = function(query) {
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

// =============================================================================
// mol.api

mol.ns('mol.api');

/**
 * Asynchronous callback that handles success and failure callbacks.
 */
mol.api.AsyncCallback = function(onSuccess, onFailure) {
    if (!(this instanceof mol.api.AsyncCallback)) {
        return new mol.api.AsyncCallback(onSuccess, onFailure);
    }
    this.onSuccess = onSuccess;
    this.onFailure = onFailure;
    return this;
};

/**
 * The API proxy used to execute requests.
 */
mol.api.ApiProxy = function() {
    if (!(this instanceof mol.api.ApiProxy)) {
        return new mol.api.ApiProxy();
    }
    this.execute = function(request, cb) {
        if (request.action === 'search') {
            var xhr = $.post('/api/taxonomy', request.params, 'json');
            xhr.success(cb.onSuccess);
            xhr.error(cb.onError);
        } else if (request.action === 'rangemap') {
            var xhr = $.post('/api/tile/metadata/'+ request.params.speciesKey);
            xhr.success(cb.onSuccess);
            xhr.error(cb.onError);
         } else if (request.action === 'points') {
            var xhr = $.post('/api/points/gbif/'+ request.params.speciesKey);
            xhr.success(cb.onSuccess);
            xhr.error(cb.onError);
        }
    };
    return this;
};

// =============================================================================
// mol.control

mol.ns('mol.control');

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
                var view = new mol.view.RangeMapView();                    
                this.activity = new mol.activity.RangeMapActivity(view);
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
                this.activity.go({params: params});
            }
        });
    return new controller();
};

// =============================================================================
// mol.event

mol.ns('mol.event');

/**
 * The event bus.
 *
 * @constructor
 */
mol.event.EventBus = function() {
    if (!(this instanceof mol.event.EventBus)) {
        return new mol.event.EventBus();
    }
    _.extend(this, Backbone.Events);
    return this;
};

// =============================================================================
// mol.view

mol.ns('mol.view');

/**
 * Search view for displaying range maps.
 * 
 * @constructor
 */
mol.view.RangeMapView = Backbone.View.extend(
{
    el: $('#map_canvas'),
    
    /**
     * Initialization.
     */
    initialize: function() {        
        var center = new google.maps.LatLng(0,0);            
        this.mapOptions = {
            zoom: 2,
            maxZoom: 20,
            center: center,
            mapTypeId: google.maps.MapTypeId.TERRAIN
        };
        this.metaControlDiv = document.createElement('div');
        var e = document.getElementById("map_canvas");
        this.map = new google.maps.Map(e, this.mapOptions);
        this.overlays = [];
    },

    renderPoints: function(json) {        
        var results = json,
            center = null,
            marker = null,
            infowin = null,
            lat = 0,
            lng = 0,
            radius = 0, 
            resources = [],
            occurrences = [],
            coordinate = null;
        for (provider in results.records.providers) {
            resources = results.records.providers[provider].resources;
            for (resource in resources) {
                occurrences = resources[resource].occurrences;
                for (coordinate in occurrences) {
                    coordinate = occurrences[coordinate].coordinates;
                    lat = parseFloat(coordinate.decimalLatitude);
                    lng = parseFloat(coordinate.decimalLongitude);
                    center = new google.maps.LatLng(lat, lng);
                    marker = new google.maps.Marker({position: center, map: this.map});
                    this.overlays.push(marker);                                                               
                }
            }
        }
    },

    initMetadata: function(metadata) {
        this.metadata = metadata;        
        this.maxZoom = this.metadata.zoom;
        this.map.mapTypes[this.map.getMapTypeId()].maxZoom = parseInt(this.maxZoom);
        this.zoomToLayerExtent();
        this.attachMetadataControl(this.metaControlDiv, this.map);
        this.map.overlayMapTypes.insertAt(0, this.rangeImageMapType());
    },

    zoomToLayerExtent: function() {
      var data = this.metadata,
          nw = data.extentNorthWest.split(','),
          se = data.extentSouthEast.split(','),
          northW = new google.maps.LatLng(parseFloat(nw[0]),parseFloat(nw[1])),
          southE = new google.maps.LatLng(parseFloat(se[0]),parseFloat(se[1])),
          bounds = new google.maps.LatLngBounds;
        bounds.extend(northW);
        bounds.extend(southE);
        this.map.fitBounds(bounds);
    },
    
    attachMetadataControl: function(div, map) {    
        var metaBtn = document.createElement('div'),
            metaText = document.createElement('div'),
            self = this;
        metaBtn.style.backgroundColor = 'white';
        metaBtn.style.borderStyle = 'solid';
        metaBtn.style.borderWidth = '1px';
        metaBtn.style.cursor = 'pointer';
        metaBtn.style.textAlign = 'center';
        metaBtn.title = 'Click for range map metadata';
        div.style.padding = '8px';    
        div.appendChild(metaBtn);
        metaText.style.fontFamily = 'Lucida Grande, Trebuchet MS';
        metaText.style.fontSize = '12px';
        metaText.style.paddingLeft = '4px';
        metaText.style.paddingRight = '4px';
        metaText.innerHTML = '<b>Metadata</b>';
        metaBtn.appendChild(metaText);
        // TODO: Dispatch event to view:
        google.maps.event.addDomListener(
            metaBtn, 'click', function() {
                alert(JSON.stringify(self.metadata));
            });
        map.controls[google.maps.ControlPosition.TOP_RIGHT].push(div);
        div.index = 1;
    },


    /**
     * Returns normalized coordinates for a given map zoom level.
     * 
     * @param coord The coordinate
     * @param zoom The current zoom level
     */
    getNormalizedCoord: function(coord, zoom) {
        var y = coord.y,
            x = coord.x,
            tileRange = 1 << zoom;
        // don't repeat across y-axis (vertically)
        if (y < 0 || y >= tileRange) {
            return null;
        }
        // repeat across x-axis
        if (x < 0 || x >= tileRange) {
            x = (x % tileRange + tileRange) % tileRange;
        }
        return {
            x: x,
            y: y
        };
    },
    
    /**
     * The Google Maps ImageMapType for range map tiles.
     */
    rangeImageMapType: function() {   
        var self = this;
        return new google.maps.ImageMapType(
            {
                getTileUrl: function(coord, zoom) {
                    var normalizedCoord = self.getNormalizedCoord(coord, zoom),
                        speciesKey = self.metadata.mol_species_id;
                    if (!normalizedCoord) {
                        return null;
                    }
                    var bound = Math.pow(2, zoom);            
                    return "/layers/" + speciesKey + ".png?" +
                        "z=" + zoom + 
                        "&x=" + normalizedCoord.x + 
                        "&y=" + (normalizedCoord.y);
                },
                tileSize: new google.maps.Size(256, 256),
                isPng: true,
                opacity: 0.5
            });
    }
});

/**
 * Search view that dispatches user events to an activity.
 * 
 * @constructor
 */
mol.view.SearchView = Backbone.View.extend(
{
    el: $('#SearchView'), 
    
    // TODO: This is not working... workaround via JQuery in initialize():
    events: {
        "keyup #searchBox": "searchBoxKeyUp",
        "click #searchButton": "searchButtonClick"
    },
    
    /**
     * Initializes the view.
     */
    initialize: function() {
        this.box = $('#searchBox');
        this.box.keyup(this.searchBoxKeyUp());
        this.button = $('#searchButton');
        this.button.click(this.searchButtonClick());
        this.checkbox = $('#cb');
        this.checkbox.change(this.searchButtonClick());
        $('#cbtext').click(this.checkBoxTextClick());
        this.tableContainer = $('#searchTable')[0];
        this.table = new google.visualization.Table(this.tableContainer);
    },
    
    checkBoxTextClick: function() {
        var self = this;
        return function(evt) {
            self.setMapsCheckbox(!self.isMapsChecked());
            self.searchButtonClick()();
        };
    },
    
    clearTable: function() {
        this.tableContainer.innerHTML = '';
    },
    
    isMapsChecked: function() {
        return this.checkbox.is(':checked');
    },
    
    setMapsCheckbox: function(isChecked) {
        this.checkbox.attr('checked', isChecked);
    },
    
    setActivity: function(activity) {
        this.activity = activity;
    },
        
    /**
     * Returns the text in the search box.
     */
    getSearchText: function() {
        return this.box.val() || this.box.attr('placeholder');
    },
    
    /**
     * Handles keyup event on the #searchBox and dispatches to activity.
     */
    searchBoxKeyUp: function(evt) {
        var self = this;
        return function(evt) {
            self.activity.searchBoxKeyUp(evt);                
        };
    },
    
    /**
     * Sets search button enabled property.
     */
    setSearchButtonEnabled: function(isEnabled) {
        var val = isEnabled ? '' : 'disabled';
        this.button.attr('disabled', val);        
    },

    /**
     * Handles click event on the #searchButton and dispatches to activity.
     */
    searchButtonClick: function(evt) {
        var self = this;
            return function(evt) {
                self.activity.searchButtonClick(evt);
            };
    },
    
    /**
     * Sets the #searchBox text.
     */
    setSearchText: function(t) {            
        this.box.val(t);
    }
});

// =============================================================================
// mol.activiy

mol.ns('mol.activity');

/**
 * The range map activity.
 * 
 * @constructor
 */
mol.activity.RangeMapActivity = function(view) {
    if (!(this instanceof mol.activity.RangeMapActivity)) {
        return new mol.activity.RangeMapActivity(view);
    }
    this.view = view;
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

/**
 * The search activity.
 * 
 * @constructor
 */
mol.activity.SearchActivity = function(view) {
    if (!(this instanceof mol.activity.SearchActivity)) {
        return new mol.activity.SearchActivity(view);
    }
    var self = this,
        addListener = google.visualization.events.addListener;
    this.view = view;
    this.view.setActivity(this);
    this.table = this.view.table;
    this.pageSize = 10;
    this.limit = 10;
    this.offset = 0;
    this.currentDataTable = null;
    this.currentPageIndex = 0;
    
    // Wires the up callback for table paging:
    addListener(this.view.table, 'page', 
                function(e) {
                    self.handlePage(e);
                });
                   
    // Configures query options:
    this.tableOptions = {
        page: 'event', 
        showRowNumber: true,
        allowHtml: true, 
        pagingButtonsConfiguration: 'both',
        pageSize: this.pageSize
    };
    
    this.updatePagingState(0);
    return this;
};

/**
 * Updates the paging state based on a page index.
 * 
 * @param pageIndex The page index
 */
mol.activity.SearchActivity.prototype.updatePagingState = function(pageIndex) {
    var pageSize = this.pageSize,
        dataTable = this.currentDataTable,
        newStartRow = -1;        
    if (pageIndex < 0) {
        return false;
    }
    if ((pageIndex == this.currentPageIndex + 1) && dataTable) {
        if (dataTable.getNumberOfRows() <= pageSize) {
            return false;
        }
    }
    this.currentPageIndex = pageIndex;
    newStartRow = this.currentPageIndex * pageSize;
    this.offset = newStartRow;
    // Note: row numbers are 1-based yet dataTable rows are 0-based.
    this.tableOptions['firstRowNumber'] = newStartRow + 1;
    return true;
};

/**
 * Sends an API request for data and draws the results via async callback.
 * 
 * @param saveLoc True to save a history location in the browser
 */
mol.activity.SearchActivity.prototype.sendAndDraw = function(saveLoc) {
    var cb = new mol.api.AsyncCallback(this.onSuccess(), this.onFailure()),
    params = this.getSearchParams(),
    historyState = this.getHistoryState();
    this.table.setSelection([]);
    mol.apiProxy.execute({action: 'search', params: params}, cb);
    if (saveLoc) {
        mol.controller.saveLocation(mol.util.serializeQuery(historyState));            
    }
};

/**
 * Handles a paging request from the table.
 * 
 * @param properties Contains the page (1, -1, or 0)
 */
mol.activity.SearchActivity.prototype.handlePage = function(properties) {
    this.view.setSearchButtonEnabled(false);
    var localTableNewPage = properties['page'], // 1, -1 or 0
        newPage = 0;
    if (localTableNewPage != 0) {
        newPage = this.currentPageIndex + localTableNewPage;
    }
    if (this.updatePagingState(newPage)) {
        this.sendAndDraw(true);
    }
};

/**
 * Goes to a place that is provided by the controller.
 * 
 * @param place The place object to go to
 */
mol.activity.SearchActivity.prototype.go = function(place) {
    var params = place.params,
        q = params.q,
        offset = Number(params.offset),
        limit = Number(params.limit),
        maps = mol.util.isBool(params.maps),
        newStartRow = -1,
        initialLoad = this.currentDataTable == null,
        pageIndex = -1,
        currentMapsValue = this.view.isMapsChecked();
    
    // Handles an initial load without params:
    if (!q && !maps) {
        this.view.setSearchText('');
        this.view.setMapsCheckbox(true);
        this.view.clearTable();
        return;
    }
    // Updates state:
    this.offset = ((offset != null) && offset >= 0) ? offset : this.offset;
    this.limit = ((limit != null) && limit >= 0) ? limit : this.limit;
    this.pageSize = this.limit;
    this.tableOptions['pageSize'] = this.pageSize;
    if (currentMapsValue != maps) {
        pageIndex = 0;
    } else {
        pageIndex = this.offset / this.pageSize;           
    }
    // Updates view:
    this.view.setSearchText(q);
    this.view.setMapsCheckbox(maps);   
    if (this.updatePagingState(pageIndex)) {
        this.sendAndDraw(true);        
    }
};

/**
 * Clicks the search button if the enter key was pressed.
 * 
 * @param evt The click event
 */
mol.activity.SearchActivity.prototype.searchBoxKeyUp = function(evt) {
    if (evt.keyCode === 13) {
        this.searchButtonClick(evt);
    }
};

/**
 * Gets the search params to be sent with an API request.
 */
mol.activity.SearchActivity.prototype.getSearchParams = function() {
    return {
        q: this.view.getSearchText(),
        limit: this.limit + 1,
        offset: this.offset,
        maps: this.view.isMapsChecked(),
        tqx: true
    };
};

/**
 * Gets the history token for saving the current location.
 */
mol.activity.SearchActivity.prototype.getHistoryState = function() {
    return {
        q: this.view.getSearchText(),
        limit: this.limit,
        offset: this.offset,
        maps: this.view.isMapsChecked(),
        tqx: true
    };
};

/**
 * Async callback for successful API requests.
 */
mol.activity.SearchActivity.prototype.onSuccess = function() {
    var self = this;
    return function(json) {
        self.view.setSearchButtonEnabled(true);
        var data = null;
        self.currentDataTable = null;
        google.visualization.errors.removeAll(self.view.tableContainer);        
        eval("data = " + json);
        self.currentDataTable = new google.visualization.DataTable(data);
        self.table.draw(self.currentDataTable, self.tableOptions);
        if (self.currentDataTable.getNumberOfRows() == 0) {
            google.visualization.errors.addError(
                self.view.tableContainer, 
                'No results',
                '', 
                {'showInTooltip': false});      
        }
    };
};

/**
 * Async callback for problematic API requests.
 */
mol.activity.SearchActivity.prototype.onFailure = function() {
    var self = this;
    return function(error) {
        alert('Failure: ' + error);
        self.view.setSearchButtonEnabled(true);
    };
};

/**
 * Handles a user search button click and also saves a browser location.
 * 
 * @param evt The button click event
 */
mol.activity.SearchActivity.prototype.searchButtonClick = function(evt) {
    this.view.setSearchButtonEnabled(false);
    this.offset = 0;
    this.currentPageIndex = 0;
    this.tableOptions['firstRowNumber'] = 1;
    this.sendAndDraw(true);
};

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