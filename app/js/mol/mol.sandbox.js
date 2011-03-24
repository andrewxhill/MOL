function MOL() {
    var args = Array.prototype.slice.call(arguments),
        callback = args.pop(),
        modules = (args[0] && typeof args[0] === "string") ? args : args[0],
        i;
    if (!(this instanceof MOL)) {
        return new MOL(modules, callback);
    }
    if (!modules || modules === '*') {
        modules = [];
        for (i in MOL.modules) {
            if (MOL.modules.hasOwnProperty(i)) {
                modules.push(i);
            }
        }
    }
    for (i = 0; i < modules.length; i += 1) {
        MOL.modules[modules[i]](this);
    }
    callback(this);
    return this;
};

// =============================================================================
// Modules

MOL.modules = {};

// =============================================================================
// Modules: Log

MOL.modules.log = function(env) {    
    env.log = {};

    env.log.write = function(msg) {
        if (env.log.enabled) {
            var logger = window.console;
            if (logger && logger.markTimeline) {
                logger.markTimeline(msg);
            }
            console.log(msg);
        }
    };

    env.log.info = function(msg) {
        env.log.write('INFO: ' + msg);
    };

    env.log.warn = function(msg) {
        env.log.write('WARN: ' + msg);
    };

    env.log.error = function(msg) {
        env.log.write('ERROR: ' + msg);
    };
    
    env.log.todo = function(msg) {
        env.log.write('TODO: '+ msg);
    };

};

// =============================================================================
// Modules: AJAX

MOL.modules.ajax = function(env) {
    env.ajax = {};

    env.ajax.Api = Class.extend(
        {
            execute: function(request, success, failure) {
                if (request.action === 'search') {
                    var xhr = $.post('/api/taxonomy', request.params, 'json');
                    xhr.success(success);
                    xhr.error(failure);
                } else if (request.action === 'rangemap-metadata') {
                    var xhr = $.post('/api/tile/metadata/'+ request.params.speciesKey);
                    xhr.success(success);
                    xhr.error(failure);
                } else if (request.action === 'gbif-points') {
                    var xhr = $.post('/api/points/gbif/'+ request.params.speciesKey);
                    xhr.success(success);
                    xhr.error(failure);
                }
            }
        }
    );    
};

// =============================================================================
// Modules: Events

MOL.modules.events = function(env) {
    env.events = {};
    
    // Backbone.js Events rip:
    env.events.Bus = Class.extend(
        {
            bind : function(ev, callback) {
                var calls = this._callbacks || (this._callbacks = {});
                var list  = this._callbacks[ev] || (this._callbacks[ev] = []);
                list.push(callback);
                return this;
            },
            
            unbind : function(ev, callback) {
                var calls;
                if (!ev) {
                    this._callbacks = {};
                } else if ((calls = this._callbacks)) {
                    if (!callback) {
                        calls[ev] = [];
                    } else {
                        var list = calls[ev];
                        if (!list) return this;
                        for (var i = 0, l = list.length; i < l; i++) {
                            if (callback === list[i]) {
                                list.splice(i, 1);
                                break;
                            }
                        }
                    }
                }
                return this;
            },
            
            trigger : function(ev) {
                var list, calls, i, l;
                if (!(calls = this._callbacks)) return this;
                if (calls[ev]) {
                    list = calls[ev].slice(0);
                    for (i = 0, l = list.length; i < l; i++) {
                        list[i].apply(this, Array.prototype.slice.call(arguments, 1));
                    }
                }
                if (calls['all']) {
                    list = calls['all'].slice(0);
                    for (i = 0, l = list.length; i < l; i++) {
                        list[i].apply(this, arguments);
                    }
                }
                return this;
            }
        }    
    );
};

// =============================================================================
// Modules: UI

MOL.modules.ui = function(env) { 
    
    env.ui = {};

    /**
     * Base class for views.
     */
    env.ui.View = Class.extend(
        {
            init: function(element) {
                this._element = element;
            },
            
            getElement: function() {
                return this._element;
            }
        }
    );

// =============================================================================
// Modules: UI - MapControl

    /**
     * The MapControl encapsulates a MapControlView and a MapControlEngine. It
     * presents a control widget on a Google Map that can be used to add, remove,
     * view, and interact with map layers.
     * 
     * @constructor
     */
    env.ui.MapControl = Class.extend(
        {
            init: function(api, bus, map) {
                this._api = api;
                this._bus = bus;
                this._map = map;
                this._view = new env.ui.MapControlView(this._viewConfig());
                this._engine = new env.ui.MapControlEngine(api, bus, this._view, map);
            },
            
            // -----------------------------------------------------------------
            // Private methods:

            _viewConfig: function() {
                return {
                    map: this._map,
                    text: {
                        addLayer: 'Add',
                        deleteLayer: 'Delete', 
                        layers:'Layers',
                        addRangeMap: 'Add range map',
                        addPoints: 'Add points',
                        go: 'Go',
                        pointsFromGbif: 'Points from GBIF'
                    }
                };
            }
        }
    );

// =============================================================================
// Modules: UI - MapControlView

    /**
     * The MapControlView encapsulates all the UI DOM stuff for presenting the
     * control widget on the Google map. It provides a public interface for 
     * accessing and controlling its various UI elements. It dispatches all 
     * UI events back down to the MapControlEngine.
     * 
     * @constructor
     */
    env.ui.MapControlView = env.ui.View.extend(
        {
            /**
             * Constructor for the MapControlView that takes a configuration 
             * object with the following properties:
             *     map - A Google Map object
             *     text - An object that contains i8ln text properties
             *      
             * @param config The configuration object
             */
            init: function(config) {
                // The top level <div> container for this view:
                var element = $('<div>')
                    .attr({'id':'layer-widget-container', 
                           'class':'widget-container'});                
                this._super(element);                
                this._config = config;
                this._layerViews = {};
                this._initUiElements();
                this._buildUi();
                this._attachToMap();
            },

            // -----------------------------------------------------------------
            // Public methods:

            setEngine: function(engine) {
                this.engine = engine;
            },
            
            getPointSearchText: function() {            
                return this._addPointsUi.find('#gbif_points_search_box').val();
            },
            
            setPointSearchText: function(value) {
                this._addPointsUi.find('#gbif_points_search_box').val(value);
            },
            
            showAddLayerUi: function() {
                this._toggleAddLayerUi(true);
            },

            hideAddLayerUi: function() {
                this._toggleAddLayerUi(false);
            },
            
            showAddPointsUi: function() {
                this._toggleAddPointsUi(true);
            },

            hideAddPointsUi: function() {
                this._toggleAddPointsUi(false);
            },
            
            addLayerView: function(layerView, id) {            
                this._list.prepend(layerView.getElement());
                this._layerViews[id] = layerView;
            },

            deleteLayerView: function(id) {
                this._layerViews[id].remove();
                this._layerViews[id] = null;
            },

            // -----------------------------------------------------------------
            // Private methods:

            /**
             * Initializes all the UI elements for this view.
             */
            _initUiElements: function() {                                
                // The top level <div> container for this._menu and this._list:
                this._layers = $('<div>')
                    .attr({'id':'layers'});
                
                // The <div> container for this._options:
                this._menu = $('<div>')
                    .attr({'id':'menu'});
                
                // The <div> container for this._addLayer and this._deleteLayer:
                this._options = $('<ul>')
                    .attr({'class': 'options list'});
                
                // An item in this._options for adding a layer:
                this._addLayer = $('<a>')
                    .attr({'id': 'add_layer', 
                           'href':'javascript:'});
                
                // An item in this._options for deleting a layer:
                this._deleteLayer = $('<a>')
                    .attr({'id': 'delete_layer', 
                           'href':'javascript:'});
                
                // The <div> container for the sortable list of layers:
                this._list = $('<div>')
                    .sortable({items: '.layer', cursor: 'move'});
                
                // The UI with options for adding a range map or points layer.
                // It is built on demand:
                this._addLayerUi = null;

                // The UI for searching and GBIF points as a layer. It is 
                // built on demand.
                this._addPointsUi = null;
                
                // The top level <div> on the Google map for adding this view:
                this._mapDiv = $('<div>')
                    .attr({'id': 'right-controller'});
            },

            /**
             * Builds the UI by combining the component elements and delegating
             * events to minimize event overhead.
             */
            _buildUi: function() {
                var self = this,
                    element = this.getElement();                
                element.disableSelection();
                $('body').append(element);
                element.append(this._layers);
                this._layers.append(this._menu);
                this._layers.append(this._list);                
                this._buildOptions();                
                this._menu.append(this._options);
                // Delegates clicks in this._options to minimize event overhead:
                element.delegate(
                    '.option.list', 'click', 
                    function(event) {
                        self._handleEvent(event);
                    }
                );
            },

            /**
             * A little helper function that builds the this._options UI.
             */
            _buildOptions: function() {
                var addText = this._config.text.addLayer,
                    deleteText = this._config.text.deleteLayer,
                    layersText = this._config.text.layers;
                this._addLayer.html(addText);
                this._deleteLayer.html(deleteText);
                // The 'Layers' item:
                this._options
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'menuLabel'})
                            .html(layersText));  
                // The 'Delete' layer item:
                this._options
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'delete'})
                            .append(this._deleteLayer)); 
                // The 'Add' layer item:
                this._options
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'add'})
                            .append(this._addLayer));               
            },

            /**
             * Builds the Add Layer UI that is used to select the type of layer
             * to add (range map or points). It's built on demand.
             */
            _buildAddLayerUi: function() {
                var buttonPoints = null,
                    buttonRange = null,
                    addRangeMapText = this._config.text.addRangeMap,
                    addPointsText = this._config.text.addPoints,
                    element = this.getElement(),
                    self = this;
                if (this._addLayerUi) {
                    return;
                }
                // The add range button:
                buttonRange = $('<button>')
                    .attr({"id":"add_range_button",
                           "class":"dialog_buttons"})
                    .html(addRangeMapText);
                // The add points button:
                buttonPoints = $('<button>')
                    .attr({"id":"add_points_button",
                           "class":"dialog_buttons"})
                    .html(addPointsText);
                // The main container:
                this._addLayerUi = $('<li>')
                    .attr({'class':'dialog list', 
                           'id':'add_new_layer_dialog'});
                this._addLayerUi.append(buttonRange);   
                this._addLayerUi.append(buttonPoints); 
                // Delegates click events for efficiency:
                element.delegate(
                    '.dialog_buttons', 'click', 
                    function(event) {
                        self._handleEvent(event);
                    }
                );            
            },

            /**
             * Builds the Add Points UI that is used to search for points to
             * to add as a new layer. It's built on demand.
             */
            _buildAddPointsUi: function() {
                var button = null,
                    input = null,
                    dialog = null,                
                    goText = this._config.text.go,
                    pointsFromGbifText = this._config.text.pointsFromGbif,
                    element = this.getElement(),
                    self = this;
                if (this._addPointsUi) {
                    return;
                }
                // The search box:
                input = $('<input>')
                    .attr({"type":"search",
                           "id":"gbif_points_search_box",
                           "value": "Puma concolor"});
                // The search button:
                button = $('<button>')
                    .attr({"id":"gbif_points_search"})
                    .html(goText);
                // The main container for the UI:
                this._addPointsUi = $('<div>')
                    .attr({"class":"dialog list", 
                           "id":"add_points_dialog"})
                    .html('<span>' + pointsFromGbifText + '</span>')
                    .append(input)
                    .append(button);
                // Delegates click events for efficiency:
                element.delegate(
                    '#gbif_points_search', 'click', 
                    function(event) {
                        self._handleEvent(event);
                    }
                );            
            },

            /**
             * For efficiency, all UI events associated with MapControlWidget
             * are delegated to this function which in turn delegates down to 
             * the engine for processing. Note that all event propogation is
             * stopped here.
             */
            _handleEvent: function(event) {
                var target = event.target;
                switch (target.id) {
                    case 'add_layer':
                    this.engine.onAddLayerClick();
                    break;
                    case 'delete_layer':
                    this.engine.onDeleteLayerClick();
                    break;
                    case 'add_points_button':
                    this.engine.onAddPointsClick();
                    break;
                    case 'add_range_button':
                    this.engine.onAddRangeClick();
                    break;
                    case 'gbif_points_search':
                    this.engine.onSearchPointsClick();
                    break;
                }
                event.stopPropagation();
            },
            
            /**
             * Attaches the MapControlWidget to the Google map.
             */
            _attachToMap: function() {
                var map = this._config.map,
                    position = google.maps.ControlPosition.TOP_RIGHT,
                    element = this.getElement();
                this._mapDiv.prepend(element);
                map.controls[position].push(this._mapDiv[0]);
            },

            /**
             * Toggles the Add Layer UI based on the 'visible' parameter.
             */
            _toggleAddLayerUi: function(visible) {
                this._buildAddLayerUi();
                if (visible) {
                    this._list.prepend(this._addLayerUi);
                } else {
                    this._addLayerUi.remove();
                }
            },
            
            /**
             * Toggles the Add Point UI based on the 'visible' parameter.
             */
            _toggleAddPointsUi: function(visible) {          
                this._buildAddPointsUi();
                if (visible) {
                    this._list.prepend(this._addPointsUi);
                } else {
                    this._addPointsUi.remove();
                }
            }
        });

// =============================================================================
// Modules: UI - MapControlEngine

    /**
     * The MapControlEngine encapsulates and drives a MapControlView. It provides
     * a public interface for handling UI events that are delivered by the view.
     * Based on the event, it updates the view to do stuff.
     * 
     * @constructor
     */
    env.ui.MapControlEngine = Class.extend( 
        {
            init: function(api, bus, view, map) {
                this._api = api;
                this._bus = bus;
                this._view = view;
                this._map = map;
                this._view.setEngine(this);
                this._layers = {};
                this._model = null;
            },

            // -----------------------------------------------------------------
            // Public methods:

            onAddLayerClick: function() {
                this._view.showAddLayerUi();
                this._model = null;
            },

            onDeleteLayerClick: function() {
                env.log.warn('Not implemented yet');
            },

            onAddPointsClick: function() {
                this._model = {type: 'points', source: 'gbif'};
                this._view.hideAddLayerUi();
                this._view.showAddPointsUi();
            },

            onAddRangeClick: function() {
                env.log.warn('Not implemented yet');
            },
            
            onSearchPointsClick: function() {
                var type = this._model.type,
                    source = this._model.source,
                    name = this._view.getPointSearchText(),
                    layer = this._createLayer(type, source, name);
                this._view.hideAddPointsUi();
                this._view.addLayerView(layer.getView(), layer.getId());
                layer.load();
            },
            
            onLayerInfoClick: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            onLayerSourceClick: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            onLayerSelected: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            onLayerChecked: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            // -----------------------------------------------------------------
            // Private methods:

            _createLayer: function(type, source, name) {
                var model = {
                    type: type,
                    source: source,
                    name: name
                };
                return new env.ui.Layer(this._api, this._bus, this._map, model);
            }
        });


    // =========================================================================
    // Modules: UI - Layer
    
    env.ui.Layer = Class.extend(
        {
            init: function(api, bus, map, model) {
                this._api = api;
                this._bus = bus;
                this._map = map;
                this._model = model;
                this._id = this._buildId(),
                this._view = new env.ui.LayerView(this._viewConfig());
                switch (model.type) {
                    case 'points':
                    this._engine = new env.ui.PointsLayerEngine(this._engineConfig());
                    break;
                    case 'range':
                    env.log.todo('Implement RangeLayerEngine');
                    break;
                }
            },
            
            // -----------------------------------------------------------------
            // Public methods:

            load: function() {
                this._engine.load();
            },

            getId: function() {
                return this._id;                
            },

            getView: function() {
                return this._view;
            },

            // -----------------------------------------------------------------
            // Private methods:

            _engineConfig: function() {
                return {
                    id: this._id,
                    model: this._model,
                    api: this._api,
                    bus: this._bus,
                    view: this._view,
                    map: this._map
                };                
            },

            _viewConfig: function() {
                return {
                    id: this._id,
                    model: this._model,
                    map: this._map,
                    text: {
                        errorTitle: 'Layer Error',
                        errorSource: 'Error Source',
                        errorDetails: 'Error Details',
                        infoTitle: 'Layer Info',
                        infoSource: 'Info Source',
                        infoDetails: 'Info Details',
                        sourceTitle: 'Layer Source',
                        sourceSource: 'Source Source',
                        sourceDetails: 'Source Details'
                    }
                };
            },

            _buildId: function() {
                var type = this._model.type,
                    source = this._model.source,
                    name = this._model.name;
                if (this.id) {
                    return this.id;                    
                }
                this.id = [type, source, name.split(' ').join('_')].join('_');
                return this.id;
            }
        }
    );

    // =========================================================================
    // Modules: UI - LayerView

    env.ui.LayerView = env.ui.View.extend( 
        {
            init: function(config) {
                var element = $("<div>")
                    .attr({"id":config.id,"class":"layer list"});
                this._super(element);
                this._config = config;
                this._map = config.map;
                this._engine = null;
                this._initUiElements();
                this._buildUi();
            },

            // -----------------------------------------------------------------
            // Public methods:
            
            setEngine: function(engine) {
                this._engine = engine;
            },

            showInfoWidget: function(fade, ms) {
                this._buildWidget('info');
                this._addToMap(this._infoWidget, fade, ms);
            },

            hideInfoWidget: function() {
                this._infoWidget.remove();
            },

            showSourceWidget: function(fade, ms) {
                this._buildWidget('source');
                this._addToMap(this._sourceWidget, fade, ms);
            },

            hideSourceWidget: function() {
                this._sourceWidget.remove();
            },

            showErrorWidget: function(fade, ms) {
                this._buildWidget('error');
                this._addToMap(this._errorWidget, fade, ms);
            },

            hideErrorWidget: function() {
                this._errorWidget.remove();
            },

            showLoadingImage: function() {
                this._loader.show();                
            },
            
            hideLoadingImage: function() {
                this._loader.hide();
            },

            showErrorButton: function() {
                this._error.show();
            },
            
            hideErrorButton: function() {
                this._error.hide();
            },

            showInfoButton: function() {
                this._info.show();
            },
            
            hideInfoButton: function() {
                this._info.hide();
            },

            showSourceButton: function() {
                this._src.show();
            },
            
            hideSourceButton: function() {
                this._src.hide();
            },

            setRadio: function(selected) {
                env.log.warn('Not implemented yet');
            },

            setChecked: function(checked) {
                this._toggle.attr('checked', checked);
            },

            enableChecked: function(enabled) {
                this._toggle.attr('enabled', enabled);
            },

            isChecked: function() {
                return this._toggle.attr('checked');
            },

            // -----------------------------------------------------------------
            // Private methods:
            
            /**
             * Initializes all the UI elements for this view.
             */
            _initUiElements: function() {
                // Div on the map for showing layer info widget:
                this._mapDiv = $('<div>')
                    .attr({'id': 'info-controller'});

                // Elements displayed in this._mapDiv:
                this._infoWidget = null;
                this._errorWidget = null;
                this._sourceWidget = null;
                
                // The radio button the selects the layer:
                this._radio = $('<input>')
                    .attr({"type":"radio",
                           "name":"active-layer",
                           "value":"points"});

                // The left container for the radio button:
                this._leftCol = $('<div>')
                    .attr({"class":"leftCol"});
                
                // Span that contains the layer name:
                this._title = $('<span>')
                    .attr({"class":"title"});
                

                // Checkbox for showing/hiding the layer on the map:
                this._toggle = $('<input>')
                    .attr({"class":"view-toggle",
                           "type":"checkbox",
                           "checked":true,
                           "id": "layer-checkbox"});
                
                // The loading gif widget:
                this._loader = $('<img>')
                    .attr({"src":"/static/loading-small.gif",
                           "class":"loading"});
                
                // The layer info button:
                this._info = $('<button>')
                    .attr({"id": "layer-info",
                           "class":"info"});

                // The Error info button:
                this._error = $('<button>')
                    .attr({"id": "layer-error",
                           "class":"error"});

                // Button for the layer source:
                this._src = $('<button>')
                    .attr({"class":"source",
                           "id": "layer-source"});
            },

            _buildUi: function() {
                var nameText = this._config.model.name,
                    typeText = this._config.model.type,
                    sourceText = this._config.model.source,
                    errorText = '!',
                    infoText = 'i',
                    infoPosition = google.maps.ControlPosition.LEFT_BOTTOM,
                    element = this.getElement(),
                    self = this;
                // Attaches this.mapDiv to the Google map:              
                this._map.controls[infoPosition].push(this._mapDiv[0]);
                // Combines elements:
                this._leftCol.append(this._radio);
                this._title.html(nameText);
                this._src.html(sourceText);
                this._info.html(infoText);
                this._error.html(errorText);
                element
                    .prepend(this._title)
                    .prepend(this._toggle)
                    .prepend(this._loader)
                    .prepend(this._error)
                    .prepend(this._info)
                    .prepend(this._src)
                    .prepend(this._leftCol);
                // Delegates events for efficiency:
                element.delegate(
                    '.view-toggle, .source, .info, .error', 'click', 
                    function(event) {
                        self._handleEvent(event);
                    }
                );
            },
            
            _buildWidget: function(type) {
                var titleText = null,
                    sourceText = null,
                    detailsText = null,
                    titleWidget = null,
                    srcWidget = null,
                    detailsWidget = null,
                    id = this._config.id,
                    el = null;
                switch (type) {
                    case 'error': // ...........................................
                    if (this._errorWidget) {
                        return;
                    }
                    this._errorWidget = $('<div>')
                        .attr({"id":id + '-error-info',
                               "class":"error"});
                    el = this._errorWidget;
                    titleText = this._config.text.errorTitle,
                    sourceText = this._config.text.errorSource,
                    detailsText = this._config.text.errorDetails;
                    break;

                    case 'info': // ............................................
                    if (this._infoWidget) {
                        return;
                    }
                    this._infoWidget = $('<div>')
                        .attr({"id":id + '-layer-info',
                               "class":"info"});                    
                    el = this._infoWidget;
                    titleText = this._config.text.sourceTitle,
                    sourceText = this._config.text.sourceSource,
                    detailsText = this._config.text.sourceDetails;
                    break;

                    case 'source': // ..........................................
                    if (this._sourceWidget) {
                        return;
                    }
                    this._sourceWidget = $('<div>')
                        .attr({"id":id + '-layer-info',
                               "class":"info"});
                    el = this._sourceWidget;
                    titleText = this._config.text.sourceTitle,
                    sourceText = this._config.text.sourceSource,
                    detailsText = this._config.text.sourceDetails;
                    break;                    
                }
                titleWidget = $('<div>').
                    attr({'id': 'infoTitle'}).
                    html(titleText);
                srcWidget = $('<div>').
                    attr({'id':'source'}).
                    html(sourceText);
                detailsWidget = $('<div>').
                    attr({'id':'details'}).
                         html(detailsText);
                el.append(titleWidget).append(srcWidget).append(detailsWidget);
            },

            _addToMap: function(element, fade, ms) {
                this._mapDiv.prepend(element[0]);
                setTimeout(
                    function() {
                        element.fadeOut(
                            fade, 
                            function() {
                                element.hide();
                            }
                        );
                    },
                    ms
                );                
            },

            /**
             * For efficiency, all UI events associated with a LayerWidget
             * are delegated to this function which in turn delegates down to 
             * the engine for processing. Note that all event propogation is
             * stopped here.
             */
            _handleEvent: function(event) {
                var target = event.target;
                switch (target.id) {
                    case 'layer-radio':
                    this._engine.onRadioClick();
                    break;
                    case 'layer-checkbox':
                    this._engine.onCheckboxClick();
                    break;
                    case 'layer-error':
                    this._engine.onErrorButtonClick();
                    break;
                    case 'layer-info':
                    this._engine.onInfoButtonClick();
                    break;
                    case 'layer-source':
                    this._engine.onSourceButtonClick();
                }
                event.stopPropagation();
            }
        }
    );
        
    // =========================================================================
    // Modules: UI - LayerEngine

    env.ui.LayerEngine = Class.extend(
        {
            init: function(config) {
                this._api = config.api;
                this._bus = config.bus;
                this._view = config.view;                
                this._map = config.map;
                this._model = config.model;
                this._id = config.id;
                this._view.setEngine(this);
                this._view.setChecked(false);
                this._view.enableChecked(false);
                this._view.hideInfoButton();
                this._view.showSourceButton();
                this._view.hideErrorButton();
                this._view.showLoadingImage();
            },
            
            // *****************************************************************
            // Abstract public methods that subclasses must override since they
            // are layer type specific:

            load: function() {
                throw 'NotImplementedError';
            },

            onCheckboxClick: function() {
                throw 'NotImplementedError';
            },

            // -----------------------------------------------------------------
            // Public methods:

            onErrorButtonClick: function() {
                this._view.showErrorWidget('slow', 8000);
            },

            onInfoButtonClick: function() {
                this._view.showInfoWidget('slow', 8000);  
            },

            onSourceButtonClick: function() {
              this._view.showSourceWidget('slow', 8000);  
            }
        }
    );

    /**
     * A LayerEngine for points.
     * 
     * @constructor 
     * @subclasses LayerEngine
     */
    env.ui.PointsLayerEngine = env.ui.LayerEngine.extend(
        {
            init: function(config) {
                this._super(config);
            },

            // -----------------------------------------------------------------
            // Public methods:

            /**
             * 
             * @override PointsLayer.onCheckboxClick
             */
            onCheckboxClick: function() {
                var checked = this._view.isChecked();
                if (checked) {
                    this._layerManager.show();
                } else {
                    this._layerManager.hide();
                }
            },

            /**
             * 
             * @override PointsLayer.load
             */
            load: function() {
                var name = this._model.name.toLowerCase(),
                    speciesKey = 'animalia/species/' + name.replace(' ', '_'),
                    params = {speciesKey: speciesKey},
                    self = this;                
                this._api.execute(
                    {action: 'gbif-points', params: params}, 
                    function(json) {
                        self._data = json;
                        var lmc = self._layerManagerConfig();
                        self._layerManager = new env.ui.PointsLayerManager(lmc);
                        self._layerManager.load();
                        self._layerManager.show();
                        self._view.hideLoadingImage();
                        self._view.showInfoButton();
                        self._view.setChecked(true);
                        self._view.enableChecked(true);
                    },
                    function(error) {
                        self._view.hideLoadingImage();
                        self._view.showErrorButton();
                    }
                );                
            },
            
            /**
             * Handles a point click by opening its info window on the map.
             * 
             * @param point
             */
            onPointClick: function(point) {
                this._layerManager.openInfoWindow(point, 'Hi!');
            },

            /**
             * Handles a point zoom by zooming to the point on the map.
             * 
             * @param point
             */
            onPointZoom: function(point) {
                this._layerManager.zoom(point, 11);
            },

            // -----------------------------------------------------------------
            // Private methods:
            
            /**
             * Returns a config object for the layer manager.
             */
            _layerManagerConfig: function() {
                return {
                    engine: this,
                    map: this._map,
                    bus: this._bus,
                    data: this._data
                };
            }
        }
    );
    
    /**
     * The LayerManager is responsible for managing the underlying data on the map.
     * It's similar to a view in that it dispatches events back down to the engine
     * and provides a public API for the engine to control it.
     * 
     * @constructor
     */
    env.ui.LayerManager = Class.extend(
        {
            init: function(config) {
                this._config = config;
                this._engine = config.engine;
                this._map = config.map;
                this._data = config.data;
                this._bus = config.bus;
            },

            // -----------------------------------------------------------------
            // Public abstract methods that must be implemented by subclasses 
            // since the functionality is layer type specific:

            show: function() {
                throw 'NotImplementedError';
            },

            hide: function() {
                throw 'NotImplementedError';
            },

            isVisible: function() {
                throw 'NotImplementedError';
            }
        }

    );

    /**
     * A LayerManager for managing points on a Google map.
     *
     * @constructor  
     * @subclasses LayerManager
     */
    env.ui.PointsLayerManager = env.ui.LayerManager.extend(
        {
            init: function(config) {
                this._super(config);
                this._overlays = [];
                this._visible = false;
            },

            // -----------------------------------------------------------------
            // Public methods:

            load: function() {
                this._load();                
            },

            isVisible: function() {
                return this._visible;
            },

            openInfoWindow: function(point, html) {
              this._openInfoWindow(point, html);  
            },

            zoom: function(point, zoomLevel) {
                self._map.setZoom(12);
                self._map.panTo(point.marker.getPosition());                 
            },

            show: function() {
                this._toggle(true);
                this._visible = true;
            },
        
            hide: function() {
                this._toggle(false);
                this._visible = false;
            },

            // -----------------------------------------------------------------
            // Private methods:

            _load: function() {
                var center = null,
                    marker = null,
                    circle = null,
                    coordinate = null,
                    resources = [],
                    occurrences = [],
                    point = {},
                    data = this._data,
                    self = this;
                for (p in data.records.providers) {
                    resources = data.records.providers[p].resources;
                    for (r in resources) {
                        occurrences = resources[r].occurrences;
                        for (o in occurrences) {
                            coordinate = occurrences[o].coordinates;
                            marker = this._createMarker(coordinate);
                            this._overlays.push(marker);                      
                            circle = this._createCircle(
                                marker.getPosition(),
                                coordinate.coordinateUncertaintyInMeters);                            
                            if (circle) {
                                this._overlays.push(circle);
                            }     
                            point = {};
                            point.marker = marker;
                            point.circle = circle;                                
                            point.sourceUrl = data.sourceUrl;
                            point.provider = data.records.providers[p];
                            point.resource = resources[r];
                            point.occurrence = occurrences[o];
                            google.maps.event.addListener(
                                marker, 
                                'click', 
                                self._createClickCallback(point)
                            );                                
                        }
                    }
                }
            },

            _createClickCallback: function(point) {
                var self = this;
                return function() {
                    self._engine.onPointClick(point);    
                };
            },

            _createCircle: function(center, coordinateUncertaintyInMeters) {          
                if (coordinateUncertaintyInMeters == null) {
                    return null;
                }
                var radius = parseFloat(coordinateUncertaintyInMeters),
                    opacity = 0.85,
                    circle = new google.maps.Circle(
                        {
                            map: null,
                            center: center,
                            radius: radius,
                            fillColor: '#CEE3F6',
                            strokeWeight: 1,                                
                            zIndex: 5
                        }
                    );
                return circle;
            },
            
            _createMarker: function(coordinate) {
                var lat = parseFloat(coordinate.decimalLatitude),
                    lng = parseFloat(coordinate.decimalLongitude),
                    center = new google.maps.LatLng(lat, lng),
                    marker = new google.maps.Marker(
                        { 
                            position: center,
                            map: null,
                            icon: 'http://labs.google.com/ridefinder/images/mm_20_red.png'
                        }
                    );
                return marker;
            },
            
            _toggle: function(visible) {
                for (x in this._overlays) {
                    if (visible) {
                        this._overlays[x].setMap(this._map);
                    } else {
                        this._overlays[x].setMap(null);
                    }
                }
            },

            _openInfoWindow: function(point, html) {
                var e = document.createElement('div'),
                    infoWin = null,
                    self = this;
                e.innerHTML = html;
                // e.getElementsByClassName('zoom')[0]
                //     .addEventListener(
                //         'click', 
                //         function() {
                //             self._engine.onPointZoom(point);
                //         }, 
                //         false);                
                infoWin = new google.maps.InfoWindow({content: e});
                infoWin.setPosition(point.marker.getPosition());
                infoWin.open(self._map, point.marker);
             }
        }
    );
};


