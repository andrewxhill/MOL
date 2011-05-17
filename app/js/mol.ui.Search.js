/**
 * Search module has a display used as a map control. It allows users to search
 * for layers to add to the map.
 */
MOL.modules.Search = function(mol) {
    
    mol.ui.Search = {};

    /**
     * Wraps a search response and surfaces an API for accessing data from it.
     */
    mol.ui.Search.Result = Class.extend(
        {
            init: function(response) {
                this._response = response;
            },

            /**
             * Gets layer names that satisfy a name, source, and type combined 
             * constraint. 
             *
             * @param name the layer name
             * @param source the layer source
             * @param type the layer type
             * @param profile the profile to test  
             * 
             */
            getLayers: function(name, source, type, profile) {
                var response = this._response,
                    currentProfile = profile ? profile : 'nameProfile',
                    nameProfile = name ? response.names[name] : null,
                    sourceProfile = source ? response.sources[source] : null,
                    typeProfile = type ? response.types[type] : null,
                    profileSatisfied = false;
                
                if (!name && !type && !source){
                    var keys = new Array();
                    for (i in response.layers) {
                        keys.push(i);
                    };
                    return keys;
                }
                
                switch (currentProfile) {
                    
                case 'nameProfile':
                    if (!name) {
                        return this.getLayers(name, source, type, 'sourceProfile');
                    }

                    if (nameProfile) {                                                
                        if (!source && !type) {
                            return nameProfile.layers;
                        }                         
                        if (source && type) {
                            if (this._exists(source, nameProfile.sources) &&
                                this._exists(type, nameProfile.types)) {
                                return _.intersect(
                                    nameProfile.layers, 
                                    this.getLayers(name, source, type, 'sourceProfile'));
                            }
                        } 
                        if (source && !type) {
                            mol.log.info('source no type');
                            if (this._exists(source, nameProfile.sources)) {
                                mol.log.info('return intersect(name.layers, sourceprofile');
                                return _.intersect(
                                   nameProfile.layers, 
                                   this.getLayers(name, source, type, 'sourceProfile'));
                            }
                        } 
                        if (!source && type) {
                            if (this._exists(type, nameProfile.types)) {
                                return _.intersect(
                                    nameProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));
                            }
                        }                            
                    } 
                    return [];                        
                    
                case 'sourceProfile':
                    if (!source) {
                        return this.getLayers(name, source, type, 'typeProfile');
                    }
                    
                    if (sourceProfile) {                        
                        if (!name && !type) {
                            return sourceProfile.layers;
                        }                         
                        if (name && type) {
                            if (this._exists(name, sourceProfile.names) &&
                                this._exists(type, sourceProfile.types)) {
                                return _.intersect(
                                    sourceProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));                                
                            }    
                        }                        
                        if (name && !type) {
                            if (this._exists(name, sourceProfile.names)) {
                                mol.log.info('returning source layers');
                                return sourceProfile.layers;
                            }
                        }                         
                        if (!name && type) {
                            if (this._exists(type, sourceProfile.types)) {
                                return _.intersect(
                                    sourceProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));                                
                            }
                        }                        
                    } 
                    return [];

                case 'typeProfile':
                    if (!type) {
                        return [];
                    }
                    
                    if (typeProfile) {
                        if (!name && !source) {
                            return typeProfile.layers;
                        }
                        if (name && source) {
                            if ( this._exists(name, typeProfile.names) &&
                                 this._exists(source, typeProfile.sources)) {
                                return typeProfile.layers;
                            }                            
                        }                         
                        if (name && !source) {
                            if (this._exists(name, typeProfile.names)) {
                                return typeProfile.layers;
                            }                            
                        }                         
                        if (!name && source) {
                            if (this._exists(source, typeProfile.sources)) {
                                return typeProfile.layers;
                            }                            
                        }                        
                    }                    
                    return [];
                } 
                return [];
            },

            getLayer: function(layer) {
                return this._response.layers[layer];
            },

            getKeys: function(id) {
                var res;
                switch(id.toLowerCase()){
                    case "types":
                        res = this._response.types;
                        break;
                    case "sources":
                        res = this._response.sources;
                        break;
                    case "names":
                        res = this._response.names;
                        break;
                    }
                return _.keys(res);   
            },
            
            getTypeKeys: function() {
                var x = this._typeKeys,
                    types = this._response.types;
                return x ? x : (this._typeKeys = _.keys(types));                
            },

            getType: function(type) {
                return this._response.types[type];
            },

            getSourceKeys: function() {
                var x = this._sourceKeys,
                    sources = this._response.sources;
                return x ? x : (this._sourceKeys = _.keys(sources));
            },
            
            getSource: function(source) {
                return this._response.sources[source];
            },
            
            getNameKeys: function() {
                var x = this._nameKeys,
                    names = this._response.names;
                return x ? x : (this._nameKeys = _.keys(names));
            },

            getName: function(name) {
                return this._response.names[name];
            },

            /**
             * Returns true if the name exists in the array, false otherwise.
             */
            _exists: function(name, array) {
                return _.indexOf(array, name) != -1;
            }
        }
    );

    /**
     * The search engine.
     */
    mol.ui.Search.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs the engine.
             * 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
                this._nameFilter = null;
                this._sourceFilter = null;
                this._typeFilter = null;
                this._resultWidgets = [];
            },

            /**
             * Starts the engine by creating and binding the display.
             *
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                var text = {
                    select: 'Select',
                    selections: ['GBIF Species Points', 'MOL Species Range'],
                    go: 'Go',
                    search: 'Search',
                    info: 'more info',
                    next: 'Next Page',
                    add: 'Add'
                };
                this._bindDisplay(new mol.ui.Search.Display(), text);
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('Search.Engine.go()');
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display, text) {                
                var widget = null,
                    result = null,
                    option = null,
                    optionsHtml = '',
                    self = this;

                this._display = display;
                display.setEngine(this);

                this._addLayerControlEventHandler();                

                display.hide();
                //display.getNextButton().hide();
                //display.getAddButton().hide();
                //display.getFiltersWidget().hide();
                display.getResultsContainer().hide();
                //display.getNavigationWidget().hide();

                // Go button
                widget = display.getGoButton();
                widget.text(text.go);
                widget.click(
                    function(event) {
                        self._onGoButtonClick();
                    }
                );

                widget = display.getSearchBox();
                
                widget.keyup(
                    function(event) {
                      if (event.keyCode === 13) {
                          self._onGoButtonClick();
                      }
                    }
                );

                // Add button:
                widget = display.getAddButton();
                widget.click(
                    function(event) {
                        self._onAddButtonClick();
                    }
                );
                
                // Close button:
                widget = display.getCloseButton();
                widget.click(
                    function(event) {
                        display.hide();
                        display.clearFilters();
                        display.clearResults();
                        display.getResultsContainer().hide();
                        //console.log('close');
                    }
                );
                  
                this._addDisplayToMap();
            },

            _onAddButtonClick: function() {
                var resultWidgets = this._resultWidgets || [],
                    rw = null,
                    result = null,
                    bus = this._bus,
                    api = this._api,
                    LayerAction = mol.ajax.LayerAction,
                    LayerEvent = mol.events.LayerEvent,
                    Layer = mol.model.Layer,
                    callback = null,
                    action = null,
                    display = this._display,
                    layer = null,
                    isChecked = false,
                    config = {
                        layer: layer
                    };

                mol.log.info('Handling add button click');
                display.getAddButton().attr('disabled', true);
                
                for (x in resultWidgets) {
                    result = resultWidgets[x];
                    rw = result.widget;
                    isChecked = rw.findChild('.checkbox').isChecked();
                    
                    if (!isChecked) {
                        continue;
                    }

                    switch (result.type) {
                    
                    case 'points':
                        action = new LayerAction('get-points', {layerName:result.name});
                        callback = this._layerActionCallback(result);
                        api.execute(action, callback);    
                        break;

                    case 'range':
                    case 'ecoregion':
                        layer = new Layer(
                            {
                                type: result.type, 
                                source: result.source, 
                                name: result.name, 
                                name2: result.name2, 
                                key_name: result.key_name
                            } 
                        );
                        config.action = 'add';
                        config.layer = layer;
                        bus.fireEvent(new LayerEvent(config));                               
                        display.getAddButton().attr('disabled', false);                        
                        break;
                    }
                }
            },
            
            _layerActionCallback: function(result) {
                var LayerAction = mol.ajax.LayerAction,
                    ActionCallback = mol.ajax.ActionCallback,
                    LayerEvent = mol.events.LayerEvent,
                    Layer = mol.model.Layer,
                    layer = null,
                    bus = this._bus,
                    action = null,
                    config = {},
                    display = this._display;

                action = new LayerAction('get-points', {layerName:result.name});
                return new ActionCallback(
                    function(response) {
                        layer = new Layer(
                            {
                                type: result.type, 
                                source: result.source, 
                                name: result.name, 
                                name2: result.name2, 
                                key_name: result.key_name,
                                json: response
                            }
                        );
                        config.action = 'add';
                        config.layer = layer;
                        bus.fireEvent(new LayerEvent(config));                               
                        display.getAddButton().attr('disabled', false);
                    },
                    function(error) {
                        mol.log.error(error);
                    }
                );
            },

            _displayPage: function(layers) {
                var display = this._display,
                    fw = null,
                    res = null,
                    typeImg = null,
                    sourceImg = null,
                    resultWidgets = null;
                
                this._resultWidgets = [];
                resultWidgets = this._resultWidgets;
                display.clearResults();

                if (layers.length==0){
                    fw = display.noMatches();
                }

                for (r in layers){
                    res = layers[r];
                    fw = display.getNewResult();
                    typeImg = fw.getTypeImg();
                    sourceImg = fw.getSourceImg();

                    resultWidgets.push(
                        {
                            widget: fw, 
                            source: res.source, 
                            type: res.type, 
                            name: res.name,
                            name2: res.name2,
                            key_name: res.key_name
                        }
                    );

                    fw.getName().text(res.name);
                    fw.getAuthor().text(res.name2);
                    fw.getInfoLink().attr("attr","/static/dead_link.html");
                    sourceImg.attr("src","/static/maps/search/" + res.source.toLowerCase() + ".png");
                    sourceImg.click(function() {
                        mol.log.todo('Send source info to LeftBottom Modal');
                    });
                    typeImg.attr("src","/static/maps/search/" + res.type.toLowerCase() + ".png");
                    typeImg.click(function(){
                        mol.log.todo('Send type info to LeftBottom Modal');
                    });
                }

                display.getResultsContainer().show();
            },

            _allTypesCallback: function(filter, name) {
                var self = this;
                return function(event) {                    
                    var fo = filter.getOptions();
                    for (o in fo) {
                        fo[o].removeStyleName("selected");
                    }
                    new mol.ui.Element(event.target).addStyleName("selected");                    
                    self._processFilterValue(name, null);
                    };
            },

            _optionCallback: function(filter, name) {                
                var self = this;
                return function(event) {
                    var fo = filter.getOptions();
                    for (o in fo){
                        fo[o].removeStyleName("selected");
                    }
                    new mol.ui.Element(event.target).addStyleName("selected");                            
                    self._processFilterValue(name, new mol.ui.Element(event.target).text());
                }; 
            },
            
            _createNewFilter: function(name, data){
                var allTypes,
                    display = this._display,
                    filter = display.getNewFilter(),
                    keys = data[name.toLowerCase()],
                    self = this,
                    option = null,
                    tmpKeys = [],
                    k = null;

                filter.getFilterName().text(name);
                filter.attr('id', name);

                allTypes = filter.getNewOption();
                allTypes.text("All " + name);
                allTypes.addStyleName("all");
                allTypes.click(this._allTypesCallback(filter, name));
                allTypes.addStyleName("selected");
                for (k in keys) {
                    tmpKeys.push(k);
                }
                tmpKeys.sort();
                for (i in tmpKeys) {
                    k = tmpKeys[i];
                    option = filter.getNewOption();
                    option.text(k);
                    option.click(this._optionCallback(filter, name));
                }
            },

            _processFilterValue: function(key, value){
                var layers = new Array(),
                    self = this,
                    tmp = null;
                
                switch(key.toLowerCase()) {
                    case "names":
                        self._nameFilter = value;
                        break;
                    case "sources":
                        self._sourceFilter = value;
                        break;
                    case "types":
                        self._typeFilter= value;
                        break;
                    default:
                        break;
                }
          
                tmp = this._result.getLayers(
                    self._nameFilter,
                    self._sourceFilter,
                    self._typeFilter);

                for (v in tmp) {
                    layers.push(this._result.getLayer(tmp[v]));
                }
                
                this._displayPage(layers);
            },

            _onGoButtonClick: function() {
                var query = this._display.getSearchBox().val(),
                    LayerAction = mol.ajax.LayerAction,
                    action = new LayerAction('search', {query: query}),
                    ActionCallback = mol.ajax.ActionCallback,
                    api = this._api,
                    callback = null,
                    display = this._display,
                    self = this,
                    fn = null;
                
                callback = new ActionCallback(
                    function(response) {
                        var Result = mol.ui.Search.Result,
                            filterNames = ['Names','Sources','Types'];
                        self._result = new Result(response),
                        self._displayPage(response.layers);
                        display.clearFilters();
                        for (i in filterNames) {
                            fn = filterNames[i];
                            self._createNewFilter(fn,response);
                        }
                    },

                    function(error) {
                        mol.log.error(error);
                    }
                );

                api.execute(action, callback);
            },

            /**
             * Fires a MapControlEvent so that the display is attached to
             * the map as a control in the TOP_LEFT position.
             */
            _addDisplayToMap: function() {
                var MapControlEvent = mol.events.MapControlEvent,
                    display = this._display,
                    bus = this._bus,
                    DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    ControlPosition = mol.ui.Map.Control.ControlPosition,
                    action = 'add',
                    config = {
                        display: display,
                        action: action,
                        displayPosition: DisplayPosition.TOP,
                        controlPosition: ControlPosition.TOP_LEFT
                    };
                bus.fireEvent(new MapControlEvent(config));     
            },

            /**
             * Adds an event handler for LayerControlEvent events so that a
             * 'add-click' action will show the search display as a control
             * on the map.
             */
            _addLayerControlEventHandler: function() {
                var display = this._display,
                    bus = this._bus,
                    LayerControlEvent = mol.events.LayerControlEvent;
                
                bus.addHandler(
                    LayerControlEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            displayNotVisible = !display.isVisible();               
                        
                        if (action === 'add-click' && displayNotVisible) {
                            display.show();
                            display.getSearchBox().focus();
                        }
                    }
                );
            }
        }
    );


    /**
     * A search result display.
     */
    mol.ui.Search.ResultWidget = mol.ui.Display.extend(
        {
            init: function() {
                this._super(this._html());
            },
            
            getCheckbox: function() {
                var x = this._checkbox,
                    s = '.checkbox';
                return x ? x : (this._checkbox = this.findChild(s));
            },
            
            getInfoLink: function() {
                var x = this._infoLink,
                    s = '.info';
                return x ? x : (this._infoLink = this.findChild(s));
            },
            
            getSourceButton: function() {
                var x = this._sourceButton,
                    s = '.source';
                return x ? x : (this._sourceButton = this.findChild(s));
            },
            
            getTypeButton: function() {
                var x = this._typeButton,
                    s = '.source';
                return x ? x : (this._typeButton = this.findChild(s));
            },
            
            getName: function() {
                var x = this._name,
                    s = '.resultNomial';
                return x ? x : (this._name = this.findChild(s));
            },
            getAuthor: function() {
                var x = this._author,
                    s = '.resultAuthor';
                return x ? x : (this._author = this.findChild(s));
            },
            getSourceImg: function() {
                var x = this._source,
                    s = '.source';
                return x ? x : (this._source = this.findChild(s));
            },
            getTypeImg: function() {
                var x = this._typeImg,
                    s = '.type';
                return x ? x : (this._typeImg = this.findChild(s));
            },

            _html: function() {
                return '<ul class="result">' + 
                       '        <div class="resultSource" ><button ><img class="source" src=""></button></div>' + 
                       '        <div class="resultType" ><button ><img class="type" src=""></button></div>' +
                       '        <div class="resultName">' + 
                       '            <div class="resultNomial" ></div>' + 
                       '            <div class="resultAuthor"></div>' + 
                       '        </div>' + 
                       '        <div class="resultLink"><a href="/static/dead_link.html" class="info">more info</a></div>' + 
                       '        <div class="buttonContainer"> ' + 
                       '            <input type="checkbox" class="checkbox" /> ' + 
                       '            <span class="customCheck"></span> ' + 
                       '        </div> ' + 
                       '    </ul>' + 
                       '<div class="break"></div>';
            }
        }
    );
                       
    /**
     * A search filter display
     */
    mol.ui.Search.FilterWidget = mol.ui.Display.extend(
        {
            init: function() {
                this._super(this._html());
                this._filterName = null;
                this._options = null;
            },

            getOptions: function() {
                if (!this._options){
                    this._options = this.findChild('.options');
                }
                return this._options.findChildren('.option');
            },
            
            getAllOption: function() {
                return this.findChild('.allOption');
            },

            getFilterName: function(n) {
                var s = '.filterName';
                if (!this._filterName){
                    this._filterName = this.findChild(s);
                }
                return this._filterName ;
                    
            },
            
            getNewOption: function() {
                if (!this._options){
                    this._options = this.findChild('.options');
                }
                var option = new mol.ui.Element();
                option.setStyleName('option');
                option.setInnerHtml(this._option());
                this._options.append(option);
                return option;
            },
            
            _option: function(){
                return '<div></div>';
            },
            
            _html: function() {
                return  '<div class="filter widgetTheme">' + 
                        '    <div class="filterName">Names</div>' + 
                        '    <div class="options"></div>' + 
                        '</div>';
            }
        }
    );

    /**
     * The search display.
     */
    mol.ui.Search.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super();
                this.setInnerHtml(this._html());
                this._config = config;
            },
            
            clearFilters: function() {
                _.each(
                    this.findChild('.filters').findChildren('.filter'),
                    function(element) {
                        element.remove();
                    }
                );
            },
            
            getFilters: function(id) {
                return this.findChild('#' + id);
            },
            
            getSearchWidget: function(){
                var x = this._searchWidget,
                    s = '.mol-LayerControl-Search';
                return x ? x : (this.searchWidget = this.findChild(s));
            },


            getResultsContainer: function(){
                var x = this._resultsContainer,
                    s = '.mol-LayerControl-Results';
                return x ? x : (this._resultsContainer = this.findChild(s));
            },


            getCloseButton: function(){
                var x = this._closeButton,
                    s = '.cancel';
                return x ? x : (this._closeButton = this.findChild(s));
            },

            getSearchBox: function(){
                var x = this._searchBox,
                    s = '.value';
                return x ? x : (this._searchBox = this.findChild(s));
            }, 
                        
            getGoButton: function() {
                var x = this._goButton,
                    s = '.execute';
                return x ? x : (this._goButton = this.findChild(s));
            },
            
            getNextButton: function() {
                var x = this._nextButton,
                    s = '.nextPage';
                return x ? x : (this._nextButton = this.findChild(s));
            },

            getAddButton: function(){
                var x = this._addButton,
                    s = '.addAll';
                return x ? x : (this._addButton = this.findChild(s));
            },
            
            clearResults: function(){
                this.findChild('.resultList').setInnerHtml("");
            },
            
            clearFilters: function(){
                this.findChild('.filters').setInnerHtml("");
            },
            
            getNewResult: function(){
                var ResultWidget = mol.ui.Search.ResultWidget,
                    r = new ResultWidget();
                this.findChild('.resultList').append(r);
                return r;
            },
            noMatches: function(){
                var r = new mol.ui.Element('<ul class="result">' + 
                                           '    <i>No matches</a>' + 
                                           '</ul>') ;
                this.findChild('.resultList').append(r);
                return r;
            },
            
            getNewFilter: function(){
                var FilterWidget = mol.ui.Search.FilterWidget,
                    r = new FilterWidget();
                this.findChild('.filters').append(r);
                return r;
            },

            _html: function(){
                return '<div class="mol-LayerControl-Search widgetTheme">' + 
                       '  <div class="title">Search:</div>' + 
                       '  <input class="value" type="text">' + 
                       '  <button class="execute">Go</button>' + 
                       '  <button class="cancel"><img src="/static/cancel.png" ></button>' + 
                       '</div>' + 
                       '<div class="mol-LayerControl-Results">' + 
                       '  <div class="filters">' + 
                       '  </div>' + 
                       '  <div class="searchResults widgetTheme">' + 
                       '    <div class="resultHeader">Results</div>' + 
                       '    <ol class="resultList"></ol>' + 
                       '    <div class="pageNavigation">' + 
                       '       <button class="addAll">Map Selected Layers</button>' + 
                       '    </div>' + 
                       '  </div>' + 
                       '</div>';
            }
        }
    );
};
