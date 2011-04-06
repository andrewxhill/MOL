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
                    for (i in response.layers) {keys.push(i)};
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

                // Add button:
                widget = display.getAddButton();
                widget.click(
                    function(event) {
                        self._onAddButtonClick();
                    }
                );

                // Restart button:
                widget = display.getRestartButton();
                widget.click(
                    function(event) {
                        // TODO
                    }
                );
                
                // Close button:
                widget = display.getCloseButton();
                widget.click(
                    function(event) {
                        display.hide();
                    }
                );
                  
                this._addDisplayToMap();
            },

            _onAddButtonClick: function() {
                var resultWidgets = this._resultWidgets || [],
                    rw = null,
                    result = null,
                    bus = this._bus,
                    LayerEvent = mol.events.LayerEvent,
                    Layer = mol.model.Layer,
                    layer = null,
                    config = {
                        layer: layer
                    };

                mol.log.info('Handling add button click');
                
                for (x in resultWidgets) {
                    result = resultWidgets[x];
                    rw = result.widget;
                    layer = new Layer(result.type, result.source, result.name);
                    config = {
                        action: 'add',
                        layer: layer
                    };
                    if (rw.findChild('.checkbox').isChecked()) {
                        bus.fireEvent(new LayerEvent(config));
                    }
                }
            },
            
            _displayPage: function(layers) {
                var display = this._display;

                display.clearResult();

                for (r in layers){
                    var res = layers[r],
                        fw = display.getNewResult(),
                        typeImg = fw.getTypeImg(),
                        sourceImg = fw.getSourceImg(),
                        resultWidgets = this._resultWidgets || [];
                    
                    resultWidgets.push({widget:fw, source:res.source, type:res.type, name:res.name});

                    fw.getName().text(res.name);
                    fw.getAuthor().text(res.name2);
                    fw.getInfoLink().attr("attr","/static/dead_link.html");
                    sourceImg.attr("src","/static/maps/search/" + res.source + ".png");
                    sourceImg.click(function(){
                        console.log('TODO: send source info to LeftBottom Modal');
                    });
                    typeImg.attr("src","/static/maps/search/" + res.type + ".png");
                    typeImg.click(function(){
                        console.log('TODO: send type info to LeftBottom Modal');
                    });
                    ///TODO: andrew
                    ///get source, type button imgs
                    ///set attr img src
                }
                //fw.getFilterName().text('Names');
                //for (k in nameKeys) {
                //    fo = fw.getNewOption();
                //    key = nameKeys[k];
                //    fo.text(key);
                //}
                display.getResultsContainer().show();
            },

            _createNewFilter: function(name, data){
                var allTypes,
                    display = this._display,
                    filter = display.getNewFilter(),
                    keys = data[name.toLowerCase()],
                    self = this;
                filter.getFilterName().text(name);
                filter.attr('id', name);
                for (k in keys) {
                    var option;
                    option = filter.getNewOption();
                    option.text(k);
                    option.click(
                        function(event) {
                            var fo = filter.getOptions();
                            for (o in fo){
                                fo[o].removeStyleName("selected");
                            }
                            new mol.ui.Element(event.target).addStyleName("selected");
                            
                            self._processFilterValue(name,new mol.ui.Element(event.target).text());
                        }
                    );
                }
                allTypes = filter.getNewOption();
                allTypes.text("All "+name);
                allTypes.addStyleName("all");
                allTypes.click(
                    function(event) {
                        var fo = filter.getOptions();
                        for (o in fo){
                            fo[o].removeStyleName("selected");
                        }
                        new mol.ui.Element(event.target).addStyleName("selected");
                        self._processFilterValue(name,null);
                    }
                );
                allTypes.addStyleName("selected");
            },

            _processFilterValue: function(key,value){
                var layers = new Array(),
                    self = this;

                key = key.toLowerCase();
                console.log([self._nameFilter,self._sourceFilter,self._typeFilter]);
                switch(key){
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
                console.log([self._nameFilter,self._sourceFilter,self._typeFilter]);
                var tmp = this._result.getLayers(self._nameFilter,self._sourceFilter,self._typeFilter);
                console.log(tmp);
                for (v in tmp){
                    console.log(v);
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
                        for (i in filterNames){
                            fn = filterNames[i];
                            self._createNewFilter(fn,response);
                        }
                        //TODO: get selected filters
                        //self._display.getSelectedFilters();
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
            },

            getOptions: function() {
                return this.findChildren('.option');
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
                var option = new mol.ui.Element();
                option.setStyleName('option');
                option.setInnerHtml(this._option());
                this.append(option);
                return option;
            },
            
            _option: function(){
                return '<div></div>';
            },
            
            _html: function() {
                return  '<div class="filter widgetTheme">' + 
                        '    <div class="filterName">Names</div>' + 
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
                    s = '#searchCancel';
                return x ? x : (this._closeButton = this.findChild(s));
            },

            getRestartButton: function(){
                var x = this._restartButton,
                    s = '#searchRestart';
                return x ? x : (this._restartButton = this.findChild(s));
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
            
            clearResult: function(){
                this.findChild('.searchResults').setInnerHtml("");
            },
            
            getNewResult: function(){
                var ResultWidget = mol.ui.Search.ResultWidget,
                    r = new ResultWidget();
                this.findChild('.searchResults').append(r);
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
                       '  <input class="value" type="text" />' + 
                       '  <button class="execute">Go</button>' + 
                       '</div>' + 
                       '<div class="mainSearchNavigation">' + 
                       '   <button id="searchCancel">' + 
                       '        <img src="/static/cancel.png" />' + 
                       '   </button>' + 
                       '   <button id="searchRestart">' + 
                       '        <img src="/static/reload.png" />' + 
                       '   </button>' + 
                       '</div>' + 
                       '<div class="mol-LayerControl-Results">' + 
                       '  <div class="filters">' + 
                       '  </div>' + 
                       '  <ol class="searchResults widgetTheme">' + 
                       '  </ol>' + 
                       '  <div class="navigation">' + 
                       '     <button class="addAll">Add</button>' + 
                       '     <button class="nextPage">More</button>' + 
                       '  </div>' + 
                       '</div>';
            }
        }
    );
};
