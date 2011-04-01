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
                display.getNextButton().hide();
                display.getAddButton().hide();
                display.getSearchResults().hide();

                // Go button
                widget = display.getGoButton();
                widget.text(text.go);
                widget.click(
                    function(event) {
                        self._onGoButtonClick();
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
                
                // Search select box:
                widget = display.getSearchSelectBox();
                this._setSearchSelectBoxOptions(widget, text.selections);
                widget.change(
                    function(event) {
                        var selection = display.getSearchSelectBox().val();
                        mol.log.info(selection + ' selected');
                    }
                );
                  
                this._addDisplayToMap();
            },
            
            _onGoButtonClick: function() {
                var query = this._display.getSearchBox().val(),
                    LayerAction = mol.ajax.LayerAction,
                    action = new LayerAction('search', {query: query}),
                    ActionCallback = mol.ajax.ActionCallback,
                    api = this._api,
                    callback = null,
                    Result = mol.ui.Search.Result,
                    result = null;
                
                callback = new ActionCallback(
                    function(response) {
                        result = new Result(response);
                        mol.log.info(
                            'Results for ' + query + ': ' 
                                + 'Names=' + result.getNameKeys() + ', ' 
                                + 'Sources=' + result.getSourceKeys() + ', '
                                + 'Types=' + result.getTypeKeys()
                        );
                    },
                    function(error) {
                        mol.log.error(error);
                    }
                );

                api.execute(action, callback);
            },

            _setSearchSelectBoxOptions: function(selectBox, options) {
                var option = null,
                    html = '';
                for (x in options) {
                    option = options[x];
                    html += '<option value="' + option + '">' 
                        + option + '</option>';
                }
                selectBox.setInnerHtml(html);
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
                        controlPosition: ControlPosition.CENTER_TOP
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
     * Mock search display for testing engine
     */
    mol.ui.Search.MockDisplay = mol.ui.Display.extend(
        {
            restartButton: {
                click: function(handler) {
                    this.restartButtonClickHandler = handler;
                },
                
                test: function() {
                    this.restartButtonClickHandler();
                }
            },
            
            getRestartButton: function() {
                return this.restartButton;
            }
        }
    );

    /**
     * A search result display.
     */
    mol.ui.Search.LayerWidget = mol.ui.Display.extend(
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

            _html: function() {
                return  '<ul class="result">' +
                    '    <div class="resultName">' +
                    '        <div class="resultNomial">Pumanator</div>' +
                    '        <div class="resultAuthor">Hill</div>' +
                    '    </div>' +
                    '    <div class="resultLink">' +
                    '      <a href="/static/dead_link.html" class="info">more info</a>' +
                    '   </div>' +
                    '    <div class="buttonContainer"> ' +
                    '        <input type="checkbox" class="checkbox" /> ' +
                    '        <span class="customCheck"></span> ' +
                    '    </div> ' +
                    '</ul>';
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
            
            getSearchWidget: function(){
                var x = this._searchWidget,
                    s = '.mol-LayerControl-Search';
                return x ? x : (this.searchWidget = this.findChild(s));
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

            getSearchText: function() {
                var x = this._searchText,
                    s = '.title';
                return x ? x : (this._searchText = this.findChild(s));
            },

            getSearchSelectBox: function() {
                var x = this._searchSelectBox,
                    s = '.source';                    
                return x ? x : (this._searchSelectBox = this.findChild(s));
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

            getMoreInfoText: function() {
                var x = this._moreInfoText,
                    s = '.resultLink';
                return x ? x : (this._moreInfoText = this.findChild(s));
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

            getSearchResults: function() {
                var x = this._searchResultsWidget,
                    s = '.searchResults';
                return x ? x : (this.searchResultsWidget = this.findChild(s));
            },

            getNewResult: function(){
                var LayerWidget = mol.ui.Search.LayerWidget,
                    r = new LayerWidget();
                this.findChild('.mol-LayerControl-Results .searchResults').append(r);
                return r;
            },

            _html: function(){
                return '<div class="mainSearchNavigation">' +
                       '    <button id="searchCancel">' +
                       '         <img src="/static/cancel.png" />' +
                       '    </button>' +
                       '    <button id="searchRestart">' +
                       '         <img src="/static/reload.png" />' +
                       '    </button>' +
                       '</div>' +
                       '<div class="mol-LayerControl-Search widgetTheme">' +
                       '   <div class="title">Search:</div>' +
                       '   <select name="source" class="source">' +
                       '       <option value="range: MOL">MOL Range Maps</option>' +
                       '       <option value="points: GBIF">GBIF Occ Points</option>' +
                       '   </select>' +
                       '   <input class="value" type="text" />' +
                       '   <button class="execute">Go</button>' +
                       '</div>' +
                       '<div class="mol-LayerControl-Results">' +
                       '   <ol class="searchResults widgetTheme">' +
                       '   </ol>' +
                       '    <div class="navigation">' +
                       '        <button class="addAll">Add</button>' +
                       '        <button class="nextPage">Next Page</button>' +
                       '    </div>' +
                       '</div>';
            }
        }
    );
};
