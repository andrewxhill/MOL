// =============================================================================
// PointsEngine object


/**
 * Constructor for PointsEngine.
 * 
 * @constructor
 * @param config Includes source, name, data, and map
 * 
 */
mol.engines.PointsEngine = function(config) {
    if (!(this instanceof mol.engines.PointsEngine)) {
        return new mol.engines.PointsEngine(config);
    }
    function F() {};        
    F.prototype = 
        { 
            type: 'points',
            source: null,
            name: null,
            data: null,
            rowId: null,
            metadata: null,
            row: null,
            map: null,
            pointsController: null,
            state: {
                NO_NAME_NO_SOURCE: 'no_name_no_source',
                SOURCE_NO_NAME: 'source_no_name',
                NAME_NO_SOURCE: 'name_no_source',
                NO_ROW: 'no_row',
                DATA_LOADING: 'data_loading',
                DATA_LOADED: 'data_loaded'
            },
            
            /**
             * Private method that builds the rowId if type, source, and name all 
             * have values. In this case true is returned. If type, source or name 
             * are undefined, then no id is created and false is returned.
             */
            buildRowId: function() {
                var type = this.type,
                source = this.source,
                name = this.name;
                if (!type || !source || !name) {
                    return false;
                }
                this.rowId = [type, source, name.split(' ').join('_')].join('_');
                return this.rowId;
            },
            
            /**
             * Private callback method that updates the row UI with a status.
             * 
             * Triggers an UPDATE_LAYER_STATUS event.
             * 
             */
            updateRowStatus: function(layerId, status, msg) {
                var self = this;
                return function(layerId, status, msg) {                            
                    if (layerId !== self.rowId) {
                        mol.log.warn('Layer id does not match');
                        return;                
                    }
                    var info = null,
                    error = null, 
                    dialog = null,
                    row = self.row;
                    switch (status) {
                    case "download-complete":
                        info = $('<button>').attr({"class":"info"}).html('i');
                        $(row).find(".loading").replaceWith(info);
                        $(info).click(
                            function() {
                                dialog = self.buildRowInfoUi();
                                mol.eventBus.trigger(
                                    mol.event.Types.ADD_CUSTOM_MAP_CONTROL, 
                                    dialog, 
                                    'info-controller');
                            }
                        );
                        mol.eventBus.bind(
                            mol.event.Types.DELETE_STACK_LAYER,
                            function(layerIdentifier) {  
                                var id = $(layerIdentifier).attr('id');
                                if (id==layerId ){
                                    this.pointsController.hideAll();
                                }
                            }
                        );
                        break;
                    case "download-error":
                        error = $('<button>').attr({"class":"error"}).html('!');
                        $(row).find(".loading").replaceWith(error);
                        $(error).click(
                            function() {
                                dialog = self.buildRowErrorUi(msg);
                                mol.eventBus.trigger(
                                    mol.event.Types.ADD_CUSTOM_MAP_CONTROL, 
                                    dialog, 
                                    'info-controller');
                            }
                        );
                        break;
                    }
                };
            }, 
            
            buildRowErrorUi: function(msg) {
                var rowId = this.rowId,
                name = this.name,
                type = this.type,
                source = this.source;
                var dialog = $('<div>').attr({"id":rowId+'-error-info',"class":"info"});
                var title = $('<div id="infoTitle">Error: '+name+" "+type+'</div>');
                var src = $('<div id="source">Source: '+source+'</div>');
                var details = $('<div id="details">Details: There was an error loading the data, '+msg+'. To replicate the query go <a href="/static/dead_link.html">here</a></div>');
                $(dialog).append(title).append(src).append(details);  
                return dialog;
            },

            buildRowInfoUi: function() {
                var rowId = this.rowId,
                name = this.name,
                type = this.type,
                source = this.source;
                var dialog = $('<div>').attr({"id":rowId+'-layer-info',"class":"info"});
                var title = $('<div id="infoTitle">Info about layer: '+name+" "+type+'</div>');
                var src = $('<div id="source">Source: '+source+'</div>');
                var details = $('<div id="details">Details: The data is the result of the work of 24 institution. To use this data you must bide by the requirements of the data providers. For the complete list of data providers, go here <a href="/static/dead_link.html">here</a></div>');
                $(dialog).append(title).append(src).append(details);
                return dialog;
            },

            /**
             * Private method that builds the row UI.
             * 
             * Binds an UPDATE_LAYER_STATUS event.
             * 
             */
            buildRowUi: function() {            
                if (!this.buildRowId()) {                
                    return;
                }
                var rowId = this.rowId,
                name = this.name,
                type = this.type,
                source = this.source,
                self = this;
                var radio = $('<input>')
                    .attr({"type":"radio","name":"active-layer","value":"points"});
                var leftCol = $('<div>')
                    .attr({"class":"leftCol"})
                    .append(radio);
                var title = $('<span>')
                    .attr({"class":"title"})
                    .html(name);
                var src = $('<button>')
                    .attr({"class":"source"})
                    .html(source);
                src.click(function(){
                              var dialog = $('<div>').attr({"id":self.rowId+'-source-info',"class":"info"});
                              var title = $('<div id="infoTitle">'+self.source+'</div>');
                              var details = $('<div id="details">Here we will give you some details about the source</div>');
                              $(dialog).append(title).append(details);
                              mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'info-controller');
                          });
                var toggle = $('<input>')
                    .attr({"class":"view-toggle","type":"checkbox","checked":true});
                toggle.click(
                    function(evt) {
                        if (evt.srcElement.checked) {
                            self.pointsController.showAll();
                        } else {
                            self.pointsController.hideAll();
                        }
                    }
                );
                var loader = $('<img>')
                    .attr({"src":"/static/loading-small.gif","class":"loading"});
                this.row = $("<div>")
                    .attr({"id":rowId,"class":"layer list"})
                    .prepend(title)
                    .prepend(toggle)
                    .prepend(loader)
                    .prepend(src)
                    .prepend(leftCol);
                mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, this.row); 
                mol.eventBus.bind(
                    mol.event.Types.UPDATE_LAYER_STATUS, self.updateRowStatus());
            },

            /**
             * Private method that builds the source UI.
             * 
             */
            buildSourceUi: function() {
                var source = this.source;
                switch (source) {
                case "GBIF":
                    this.buildGbifSourceUi();
                }
            },

            /**
             * Private method that builds the GBIF source UI. 
             * 
             * Triggers an ADD_NEW_STACK_LAYER event with itself as the parameter.
             * 
             * Note: This UI has a button that when clicked triggers a 
             * DELETE_STACK_LAYER event passing itself as the parameter. It also
             * calls setName() which results in buildRowUi() getting called.
             * 
             */
            buildGbifSourceUi: function() {
                var button = null,
                input = null,
                dialog = null,                
                rowId = this.rowId,
                name = this.name,
                type = this.type,
                source = this.source,
                row = this.row,
                self = this;
                if (name) {
                    return;
                }
                button = $('<button>').attr({"id":"gbif_points_search"}).html('Go');
                input = $('<input>')
                    .attr({"type":"search",
                           "id":"gbif_points_search_box",
                           "value": "Puma concolor"});
                dialog = $('<div>')
                    .attr({"class":"dialog list", "id":"add_points_dialog"})                       
                    .html('<span>Get Points From GBIF</span>')
                    .append(input)
                    .append(button);
                $(button).click(
                    function() {
                        var layerName = $(input).val();
                        mol.log('LAYER NAME ' + layerName);
                        if (!layerName) {
                            mol.log.warn('No input available in: ' + input[0].attr('id'));
                            return;
                        }
                        mol.log('Trigger ' + mol.event.Types.DELETE_STACK_LAYER);
                        mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, ".dialog");   
                        self.setName(layerName);
                    });
                mol.log('Trigger: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
                mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, dialog);   
            },

            /**
             * Private method that returns the current engine state.
             * 
             */
            getCurrentState: function() {
                var currentState = null,
                source = this.source,
                name = this.name,
                row = this.row,
                data = this.data,
                state = this.state;
                if (source && !name) {
                    currentState = state.SOURCE_NO_NAME;
                } else if (name && !source) {
                    currentState = state.NAME_NO_SOURCE;
                } else if (!name && !source) {
                    currentState = state.NO_NAME_NO_SOURCE;  
                } else if (source && name && !row) {
                    currentState = state.NO_ROW;                
                } else if (source && name && row && data) {
                    currentState = state.DATA_LOADED;
                } else if (source && name && row && !data) {
                    currentState = state.DATA_LOADING;
                }                        
                return currentState;
            },

            /**
             * Private method that performs an engine state transition based on the 
             * current state.
             * 
             */
            transition: function() {
                var currentState = this.getCurrentState(),
                state = this.state;
                mol.log('Engine state transition: ' + currentState);
                switch (currentState) {
                case state.SOURCE_NO_NAME:
                case state.NO_NAME_NO_SOURCE:
                    this.buildSourceUi();
                    break;
                case state.NAME_NO_SOURCE:
                    // TODO: How handle this?
                    break;
                case state.NO_ROW:
                    this.buildRowUi();
                    this.loadGbifPointData();
                    this.transition();
                case state.DATA_LOADING:
                    break;
                case state.DATA_LOADED:
                    break;
                }
            },

            /**
             * Private method that loads GBIF point data asynchronously. On success, 
             * this.data is set
             * 
             * Triggers an UPDATE_LAYER_STATUS event on success or failure.
             * 
             * Invokes a state transition on success or failure.
             * 
             */
            loadGbifPointData: function() {
                var speciesKey = 'animalia/species/' + this.name.replace(' ', '_').toLowerCase(),
                params = {speciesKey: speciesKey},
                data = this.data,
                pointsController = this.pointsController,
                rowId = this.rowId,
                self = this,
                cb = new mol.api.AsyncCallback(
                    // Success callback:
                    function(json) { 
                        self.data = json;
                        if (self.data.totalRecords == 0) {
                            self.data = null;
                            self.transition();
                            mol.eventBus.trigger(
                                mol.event.Types.UPDATE_LAYER_STATUS,
                                self.rowId,
                                'download-error',
                                'No results');
                            return;
                        }
                        self.pointsController = new mol.maps.controllers.PointsController({data:json});
                        self.transition();
                        mol.eventBus.trigger(
                            mol.event.Types.UPDATE_LAYER_STATUS,
                            self.rowId,
                            'download-complete',
                            'Success');
                    },
                    // Failure callback:
                    function(error) { 
                        self.data = null;
                        self.transition();
                        mol.eventBus.trigger(
                            mol.event.Types.UPDATE_LAYER_STATUS,
                            self.rowId,
                            'download-error',
                            'Error: HTTP status ' + error.status);
                    });
                mol.apiProxy.execute({action: 'gbif-points', params: params}, cb);
                                    
            },

            /**
             * Public method that initializes the engine with a source, name, and 
             * data and immediately transitions.
             * 
             */
            init: function(config) {
                this.source = config.source;
                this.name = config.name;
                this.data = config.data;
                this.map = config.map;
                this.transition();
            },

            /**
             * Public getter and setters.
             */
            getType: function() {
                return this.type;
            },
            getSource: function() {
                return this.source;
            },
            // Note: This method causes a state transition:
            setSource: function(val) {
                this.source = val;
                this.transition();
            },
            getName: function() {
                return this.name;
            },
            // Note: This method causes a state transition:
            setName: function(val) {
                this.name = val;                  
                this.transition();
            },
            getData: function() {
                return this.data;
            },
            getRowId: function() {
                return this.rowId;
            },
            getMetadata: function() {
                return this.metadata;
            },
            setMetadata: function(val) {
                this.metadata = val;        
            }, 
            getRow: function() {
                return this.row;
            }
        };
    this.f = new F();
    this.f.init(config);
    return this.f;

};

mol.engines.RangeEngine = function(source, name, data) {
    if (!(this instanceof mol.engines.RangeEngine)) {
        return new mol.engines.RangeEngine(source, name, data);
    }
    this.init(source, name, data);
    return this;
};
/**
 * Prototype for RangeEngine
 */
mol.engines.RangeEngine.prototype = (
    function () {
        var type = 'range',
            source = null,
            name = null,
            data = null,
            rowId = null,
            metadata = null,
            row = null,
            state = {
                NO_NAME_NO_SOURCE: 'no_name_no_source',
                SOURCE_NO_NAME: 'source_no_name',
                NAME_NO_SOURCE: 'name_no_source',
                NO_ROW: 'no_row',
                DATA_LOADING: 'data_loading',
                DATA_LOADED: 'data_loaded'
            };
        
        /**
         * Private method that builds the rowId if type, source, and name all 
         * have values. In this case true is returned. If type, source or name 
         * are undefined, then no id is created and false is returned.
         */
        var buildRowId = function() {
            if (!type || !source || !name) {
                return false;
            }
            rowId = [type, source, name.split(' ')].join('_');
            return true;
        };

        /**
         * Private callback method that updates the row UI with a status.
         * 
         * Triggers an UPDATE_LAYER_STATUS event.
         * 
         */
        var updateRowStatus = function(layerId, status, msg) {
            if (layerId !== this.rowId) {
                mol.log.warn('Layer id does not match');
                return;                
            }
            var info = null,
                error = null,
                row = this.row;
            switch (status) {
            case "download-complete":
                info = $('<button>').attr({"class":"info"}).html('i');
                $(row).find(".loading").replaceWith(info);
                $(info).click(function(){
                    var dialog = $('<div>').attr({"id":rowId+'-layer-info',"class":"info"});
                    var title = $('<div id="infoTitle">Info about layer: '+name+" "+type+'</div>');
                    var src = $('<div id="source">Source: '+source+'</div>');
                    var details = $('<div id="details">Details: Some info about the range provenance</div>');
                    $(dialog)
                        .append(title)
                        .append(src)
                        .append(details)
                    mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'info-controller');
                });
                break;
            case "download-error":
                error = $('<button>').attr({"class":"error"}).html('!');
                $(row).find(".loading").replaceWith(error);
                $(error).click(function(){
                    var dialog = $('<div>').attr({"id":rowId+'-error-info',"class":"info"});
                    var title = $('<div id="infoTitle">Error: '+name+" "+type+'</div>');
                    var src = $('<div id="source">Source: '+source+'</div>');
                    var details = $('<div id="details">Details: There was an error loading the data, '+msg+'. To replicate the query go <a href="/static/dead_link.html">here</a></div>');
                    $(dialog)
                        .append(title)
                        .append(src)
                        .append(details)
                    mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'info-controller');
                });
                break;
            }
            mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, row); 
            /* show the widget when loading is complete */
            //mol.eventBus.trigger(mol.event.Types.CONTROLLER_FOCUS_UPDATE,rowId, true);   
            //mol.eventBus.trigger(mol.event.Types.CONTROLLER_FOCUS_UPDATE,rowId, false, true);   
        };    

        /**
         * Private method that builds the row UI.
         * 
         * Binds an UPDATE_LAYER_STATUS event.
         * 
         */
        var buildRowUi = function() {            
            if (!buildRowId()) {                
                return;
            }
            var radio = $('<input>')
                .attr({"type":"radio","name":"active-layer","value":"range"});
            var leftCol = $('<div>')
                .attr({"class":"leftCol"})
                .append(radio);
            var title = $('<span>')
                .attr({"class":"title"})
                .html(name);
            var src = $('<button>')
                .attr({"class":"source"})
                .html(source);
            src.click(function(){
                var dialog = $('<div>').attr({"id":rowId+'-source-info',"class":"info"});
                var title = $('<div id="infoTitle">'+source+'</div>');
                var details = $('<div id="details">Here we will give you some details about the source</div>');
                $(dialog)
                    .append(title)
                    .append(details)
                mol.eventBus.trigger(mol.event.Types.ADD_CUSTOM_MAP_CONTROL, dialog, 'info-controller');
            });
            var toggle = $('<input>')
                .attr({"class":"view-toggle","type":"checkbox","checked":true});
            var loader = $('<img>')
                .attr({"src":"/static/loading-small.gif","class":"loading"});
            row = $("<div>")
                .attr({"id":rowId,"class":"layer list"})
                .prepend(title)
                .prepend(toggle)
                .prepend(loader)
                .prepend(src)
                .prepend(leftCol);
            mol.eventBus.bind(
                mol.event.Types.UPDATE_LAYER_STATUS, updateRowStatus);
        };

        /**
         * Private method that builds the source UI.
         * 
         */
        var buildSourceUi = function() {
            switch (source) {
            case "MOL":
                buildMolSourceUi();
            }
        };

        /**
         * Private method that builds the GBIF source UI. 
         * 
         * Triggers an ADD_NEW_STACK_LAYER event with itself as the parameter.
         * 
         * Note: This UI has a button that when clicked triggers a 
         * DELETE_STACK_LAYER event passing itself as the parameter. It also
         * calls setName() which results in buildRowUi() getting called.
         * 
         */
        var buildMolSourceUi = function() {
            var button = null,
                input = null,
                dialog = null;
            if (name) {
                return;
            }
            button = $('<button>').attr({"id":"mol_range_search"}).html('Go');
            input = $('<input>')
                .attr({"type":"search",
                       "id":"mol_range_search_box",
                       "value": "Puma concolor"});
            dialog = $('<div>')
                .attr({"class":"dialog list", "id":"add_range_dialog"})                       
                .html('<span>Get Range from MOL</span>')
                .append(input)
                .append(button);
            $(button).click(
                function() {
                    var layerName = $(input).val();
                    mol.log(layerName);
                    if (!layerName) {
                        mol.log.warn('No input available in: ' + input[0].attr('id'));
                        return;
                    }
                    mol.log('Trigger ' + mol.event.Types.DELETE_STACK_LAYER);
                    mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, ".dialog");   
                    setName(layerName);
                });
            mol.log('Trigger: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
            mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, dialog);   
        };

        /**
         * Private method that returns the current engine state.
         * 
         */
        var getCurrentState = function() {
            var currentState = null;
            if (source && !name) {
                currentState = state.SOURCE_NO_NAME;
            } else if (name && !source) {
                currentState = state.NAME_NO_SOURCE;
            } else if (!name && !source) {
                currentState = state.NO_NAME_NO_SOURCE;  
            } else if (source && name && !row) {
                currentState = state.NO_ROW;                
            } else if (source && name && row && data) {
                currentState = state.DATA_LOADED;
            } else if (source && name && row && !data) {
                currentState = state.DATA_LOADING;
            }                        
            return currentState;
        };

        /**
         * Private method that performs an engine state transition based on the 
         * current state.
         * 
         */
        var transition = function() {
            var currentState = getCurrentState();
            mol.log('Engine state transition: ' + currentState);
            switch (currentState) {
                case state.SOURCE_NO_NAME:
                case state.NO_NAME_NO_SOURCE:
                buildSourceUi();
                break;
                case state.NAME_NO_SOURCE:
                // TODO: How handle this?
                break;
                case state.NO_ROW:
                buildRowUi();
                loadMolRangeData();
                transition();
                case state.DATA_LOADING:
                break;
                case state.DATA_LOADED:
                break;
            }
        };

        /**
         * Private method that loads GBIF point data asynchronously. On success, 
         * this.data is set
         * 
         * Triggers an UPDATE_LAYER_STATUS event on success or failure.
         * 
         * Invokes a state transition on success or failure.
         * 
         */
        this.loadMolRangeData = function() {
            var speciesKey = 'animalia/species/' + name.replace(' ', '_').toLowerCase(),
                params = {speciesKey: speciesKey},
                cb = new mol.api.AsyncCallback(
                    // Success callback:
                    function(json) { 
                        data = json;
                        transition();
                        mol.eventBus.trigger(
                            mol.event.Types.UPDATE_LAYER_STATUS,
                            rowId,
                            'download-complete',
                            'Success');
                    },
                    // Failure callback:
                    function(error) { 
                        data = null;
                        transition();
                        mol.eventBus.trigger(
                            mol.event.Types.UPDATE_LAYER_STATUS,
                            rowId,
                            'download-error',
                            'Error: ' + error);
                    });
            mol.apiProxy.execute({action: 'rangemap-metadata', params: params}, cb);            
        };

        /**
         * Public method that initializes the engine with a source, name, and 
         * data and immediately transitions.
         * 
         */
        var init = function(initSource, initName, initData) {
            source = initSource;
            name = initName;
            data = initData;
            transition();
        };

        /**
         * Public getter and setters.
         */
        var getType = function() {
            return type;
        };
        var getSource = function() {
            return source;
        };
        // Note: This method causes a state transition:
        var setSource = function(val) {
            source = val;
            transition();
         };
        var getName = function() {
            return name;
        };
        // Note: This method causes a state transition:
        var setName = function(val) {
            name = val;        
            transition();
        };
        var getData = function() {
            return data;
        };
        var getRowId = function() {
            return rowId;
        };
        var getMetadata = function() {
            return metadata;
        };
        var setMetadata = function(val) {
            metadata = val;        
        };    
        var getRow = function() {
            return row;
        };
        

        /**
         * This is the object that is exposed publically as the prototype. So 
         * everything in this object is public. Everthing else is private by
         * enclosure.
         * 
         */
        return {            
            init: init,
            getType: getType,
            getSource: getSource,
            setSource: setSource,
            getName: getName,
            setName: setName,
            getData: getData,
            getRowId: getRowId,
            getMetadata: getMetadata,
            setMetadata: setMetadata,
            getRow: getRow
        };
    }
)();
