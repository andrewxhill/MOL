// =============================================================================
// PointsEngine object


/**
 * Constructor for PointsEngine.
 * 
 * @constructor
 * @param source The data source
 * 
 */
mol.engines.PointsEngine = function(source, name, data) {
    if (!(this instanceof mol.engines.PointsEngine)) {
        return new mol.engines.PointsEngine(source, name, data);
    }
    this.init(source, name, data);
    return this;
};

/**
 * Prototype for PointsEngine
 */
mol.engines.PointsEngine.prototype = (
    function () {
        var type = 'points',
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
            if (layerId !== rowId) {
                mol.log.warn('Layer id does not match');
                return;                
            }
            var info = null,
                error = null;
            switch (status) {
            case "download-complete":
                info = $('<button>').attr({"class":"info"}).html('i');
                $(row).find(".loading").replaceWith(info);
                break;
            case "download-error":
                error = $('<button>').attr({"class":"error"}).html('!');
                $(row).find(".loading").replaceWith(error);
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
            case "GBIF":
                buildGbifSourceUi();
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
        var buildGbifSourceUi = function() {
            var button = null,
                input = null,
                dialog = null;
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
                .html('<span>Get Points From GBIF Range</span>')
                .append(input)
                .append(button);
            $(button).click(
                function() {
                    var layerName = $(input).val();
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
                loadGbifPointData();
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
        this.loadGbifPointData = function() {
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
            mol.apiProxy.execute({action: 'gbif-points', params: params}, cb);            
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


// =============================================================================
// RangeEngine object

/**
 * Constructor for a RangeEngine.
 * 
 * @constructor
 * @param source The data source
 * 
 */
mol.engines.RangeEngine = function(source,name,data) {
    this.type = 'range';
    this._name, this._source, this._id, this._data, this._metadata;
    
    /* Some examples setter/getters */
    this.id = function(id){
        if (id){
            this._id = id;
        } else {
            return this._id;
        }
    }
    
    this.data = function(data){
        if (data){
            this._data = data;
        } else {
            return this._data;
        }
    }
    if (data) this.data(data);
    
    this.metadata = function(metadata){
        if (metadata){
            this._metadata = metadata;
        } else {
            return this._metadata;
        }
    }
    
    this.name = function(name){
        if (name){
            this._name = name;
            if (!this._id) {
                this._id = this.type + '_' + this._source + '_' + this._name.split(' ').join('_');
            }
            var radio = $('<input>')
                            .attr({"type":"radio","name":"layer-toggle","value":"range"});
            var leftCol = $('<div>')
                            .attr({"class":"leftCol"})
                            .append(radio);
            var title = $('<span>')
                            .attr({"class":"title"})
                            .html(this._name);
            var src = $('<button>')
                            .attr({"class":"source"})
                            .html(this._source);
            var toggle = $('<input>')
                            .attr({"class":"toggle","type":"checkbox","checked":true});
                            
            var loader = $('<img>')
                            .attr({"src":"/static/loading-small.gif","class":"loading"});
                            
            this.row = $("<div>")
                            .attr({"id":this._id,"class":"layer list"})
                            .prepend(title)
                            .prepend(toggle)
                            .prepend(loader)
                            .prepend(src)
                            .prepend(leftCol);
                              
            var self = this;
            mol.eventBus.bind(
                mol.event.Types.UPDATE_LAYER_STATUS, 
                function(layerId, status, msg) {
                    mol.log('Map handling event: ' + 
                                 mol.event.Types.UPDATE_LAYER_STATUS);
                    console.log(layerId);
                    console.log($(self.row));
                    if(layerId == $(self.row).attr('id')){
                        switch (status) {
                            case "download-complete":
                                var info = $('<button>')
                                                .attr({"class":"info"})
                                                .html('i');
                                $(self.row).find(".loading").replaceWith(info);
                                break;
                            case "download-error":
                                console.log('hi');
                                var error = $('<button>')
                                                .attr({"class":"error"})
                                                .html('!');
                                console.log(error);
                                $(self.row).find(".loading").replaceWith(error);
                                break;
                        }
                        mol.eventBus.trigger(mol.event.Types.SHOW_LAYER_STACK);
                    }
                }
            );  
            
            mol.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
            mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, this.row); 
                
        } else {
            return this._name;
        }
    }
    if (name) this.name(name);
    
    this.source = function(source,name,data){
        self = this;
        if (source){
            this._source = source;
            switch (this._source) {
                case "MOL":
                    if (!this._name) {
                        var button = $('<button>')
                                        .attr({"id":"mol_range_search"})
                                        .html('Go');  
                        var input = $('<input>')
                                        .attr({
                                            "type":"search",
                                            "id":"mol_range_search_box",
                                            "value": "Puma concolor"
                                            });
                        var dialog = $('<div>')
                                        .attr({"class":"dialog list","id":"add_range_dialog"})
                                        .html('<span>Get Species Range</span>')
                                        .append(input)
                                        .append(button);
                        $(button).click(function(){
                            if (!$(input).val()){
                                mol.log('No input available in: ' + $(input).attr('id'));
                            } else {
                                mol.log('Layer triggering event: ' + mol.event.Types.DELETE_STACK_LAYER);
                                mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, ".dialog");   
                                self.name($(input).val());
                            }
                        });
                        mol.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
                        mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, dialog);  
                    } else {
                        // TODO
                    }
                    break;
            }
        } else {
            return this._source;
        }
    }
    if (source) this.source(source);
};

/**
 * Shows a UI for a RangeEngine.
 * 
 */
mol.engines.RangeEngine.prototype.showUi = function() {
    var dialog = $("div");
    $(dialog).append($('<div id="add_range_dialog" class="dialog_button output">Get MOL Range Map<input type="search" id="mol_range_search_box"><a href="javascript:" id="mol_range_search">Go</a></div></div>'));
};
