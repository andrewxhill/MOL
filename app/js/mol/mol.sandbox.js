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

MOL.modules = {};

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
};

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

MOL.modules.ui = function(env) { 
    
    env.ui = {};

    /**
     * Base class for views.
     */
    env.ui.View = Class.extend(
        {
            init: function(root) {
                this.root = root;
            },
            
            getRoot: function() {
                return this.root;
            }
        }
    );

    /**
     * Interface for map control view implementations.
     */
    env.ui.MapControlViewInterface = Class.extend(
        {
            init: function(config) {},
            setEngine: function(engine) {},
            getPointsSearchText: function() {},
            setPointsSearchText: function(value) {},
            toggleAddLayerUi: function(visible) {},
            toggleAddPointsUi: function(visible) {},
            addLayerView: function(layerView) {},
            deleteLayer: function(layerId) {}
        }
    );

    /**
     * Default implementation of MapControlViewInterface.
     */
    env.ui.MapControlView = env.ui.View.extend(
        {
            init: function(config) {
                this._super($('<div>'));
                this.config = config;
                this.buildUi();
            },
        
            buildUi: function() {
                var self = this;
                this.root.attr({'id':'layer-widget-container', 
                                'class':'widget-container'});
                $(this.root).disableSelection();
                this.menu = $('<div>').attr({'id':'menu'});                    
                this.buildOptions();
                $(this.menu).append(this.options);
                this.layers = $('<div>').attr({'id':'layers'});   
                $(this.layers).append(this.menu);
                this.list = $('<div>').attr({'id':'list'});
                $(this.list).sortable({items: '.layer', cursor: 'move'});
                $(this.layers).append(this.list);
                $(this.root).append(this.layers);
                $('body').append(this.root);
                // Delegates 'Add', 'Delete', and 'Layer' button clicks to root:
                $(this.root).delegate(
                    '.option.list', 'click', 
                    function(event) {
                        self.handleClickDelegates(event);
                    }
                );
            },

            buildOptions: function() {
                var addText = this.config.text.addLayer,
                    deleteText = this.config.text.deleteLayer,
                    layersText = this.config.text.layers;
                this.options = $('<ul>').attr({'class': 'options list'});       
                this.addLayer = $('<a>')
                    .attr({'id': 'add_layer', 
                           'href':'javascript:'})
                    .html(addText);
                this.deleteLayer = $('<a>')
                    .attr({'id': 'delete_layer', 
                           'href':'javascript:'})
                    .html(deleteText);
                $(this.options)
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'menuLabel'})
                            .html(layersText));  
                $(this.options)
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'delete'})
                            .append(this.deleteLayer)); 
                $(this.options)
                    .append($('<li>')
                            .attr({'class':'option list',
                                   'id':'add'})
                            .append(this.addLayer));               
            },

            addLayerVisible: function() {
                return $("#layers").find("#add_new_layer_dialog").length > 0;
            },

            handleClickDelegates: function(event) {
                var target = event.target;
                switch (target.id) {
                    case 'add_layer':
                    this.engine.onAddButtonClick();
                    break;
                    case 'delete_layer':
                    this.engine.onDeleteButtonClick();
                    break;
                    case 'add_points_button':
                    this.engine.onAddPointsButtonClick();
                    break;
                    case 'add_range_button':
                    this.engine.onAddRangeMapButtonClick();
                    break;
                }
                event.stopPropagation();
                event.preventDefault();
            },

            setEngine: function(engine) {
                this.engine = engine;
            },
            
            getPointsSearchText: function() {            
                env.log.warn('Not implemented yet');
            },
            
            setPointsSearchText: function(value) {
                env.log.warn('Not implemented yet');
            },
           
            buildAddLayerUi: function() {
                var dialog = null,
                    buttonPoints = null,
                    buttonRange = null,
                    addRangeMap = this.config.text.addRangeMap,
                    addPoints = this.config.text.addPoints,                    
                    self = this;
                if (this.addLayerUi) {
                    return;
                }
                dialog = $('<li class="dialog list" id="add_new_layer_dialog">');
                buttonRange = $('<button>')
                    .attr({"id":"add_range_button",
                           "class":"dialog_buttons"})
                    .html(addRangeMap);
                buttonPoints = $('<button>')
                    .attr({"id":"add_points_button",
                           "class":"dialog_buttons"})
                    .html(addPoints);
                $(dialog).append(buttonRange);   
                $(dialog).append(buttonPoints); 
                this.addLayerUi = dialog;
                // Delegates 'Add points' and 'Add range map' clicks to root:
                $(this.root).delegate(
                    '.dialog_buttons', 'click', 
                    function(event) {
                        self.handleClickDelegates(event);
                    }
                );            
            },

            toggleAddLayerUi: function(visible) {
                this.buildAddLayerUi();
                if (visible) {
                    $(this.list).prepend($(this.addLayerUi));
                } else {
                    $(this.addLayerUi).remove();
                }
            },
            
            toggleAddPointsUi: function(visible) {          
                env.log.warn('Not implemented yet');
            },
            
            addLayerView: function(layerView) {            
                env.log.warn('Not implemented yet');
            },

            deleteLayer: function(layerId) {
                env.log.warn('Not implemented yet');                
            }
        });

    env.LayerView = env.ui.View.extend( 
        {
            init: function(root) {
            },
            
            setLoading: function(loading) {
                env.log.warn('Not implemented yet');
            },

            setSelectionRadio: function(selected) {
                env.log.warn('Not implemented yet');
            },

            setVisibilityCheckbox: function(checked) {
                env.log.warn('Not implemented yet');
            },

            toggleInfoUi: function(visible) {
                env.log.warn('Not implemented yet');
            },

            toggleSourceUi: function(visible) {
                env.log.warn('Not implemented yet');
            }
        }
    );
        

    /**
     * Interface for map control engine implementations.
     */
    env.ui.MapControlEngineInterface = Class.extend( 
        {
            init: function(api, bus, view, map) {},
            onAddButtonClick: function() {},
            onDeleteButtonClick: function() {},
            onAddPointsButtonClick: function() {},
            onAddRangeMapButtonClick: function() {},
            onPointsSearchButtonClick: function() {},
            onLayerInfoClick: function(layerId) {},
            onLayerSourceClick: function(layerId) {},
            onLayerRadioClick: function(layerId) {},
            onLayerCheckboxClick: function(layerId) {}
        }
    );

    /**
     * The default MapControlEngine implementation.
     */
    env.ui.MapControlEngine = Class.extend( 
        {
            init: function(api, bus, view, map) {
                this.api = api;
                this.bus = bus;
                this.view = view;
                this.map = map;
                this.view.setEngine(this);
            },

            onAddButtonClick: function() {
                this.view.toggleAddLayerUi(true);
            },

            onDeleteButtonClick: function() {
                env.log.warn('Not implemented yet');
            },

            onAddPointsButtonClick: function() {
                env.log.warn('Not implemented yet');
            },

            onAddRangeMapButtonClick: function() {
                env.log.warn('Not implemented yet');
            },
            
            onPointsSearchButtonClick: function() {
                env.log.warn('Not implemented yet');
            },
            
            onLayerInfoClick: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            onLayerSourceClick: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            onLayerRadioClick: function(layerId) {
                env.log.warn('Not implemented yet');
            },

            onLayerCheckboxClick: function(layerId) {
                env.log.warn('Not implemented yet');
            }

        });

    env.ui.MapControl = Class.extend(
        {
            init: function(api, bus, map) {
                this.api = api;
                this.bus = bus;
                this.map = map;
                this.view = new env.ui.MapControlView(this.viewConfig());
                this.engine = new env.ui.MapControlEngine(api, bus, this.view, map);
            },
            
            viewConfig: function() {
                return {
                    text: {
                        addLayer: 'Add',
                        deleteLayer: 'Delete', 
                        layers:'Layers',
                        addRangeMap: 'Add range map',
                        addPoints: 'Add points'
                    }
                };
            }
        }
    );
};


