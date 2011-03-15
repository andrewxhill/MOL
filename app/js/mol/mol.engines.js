// =============================================================================
// PointsEngine object

/**
 * Constructor for PointsEngine.
 * 
 * @constructor
 * @param source The data source
 * 
 */
mol.engines.PointsEngine = function(source,name,data) {
    this.type = 'points';
    this._name, this._source, this._id, this._data, this.row;
    
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
            console.log(name);
            if (!this._id) {
                this._id = this.type + '_' + this._source + '_' + this._name.split(' ').join('_');
            }
            
            var radio = $('<input>')
                            .attr({"type":"radio","name":"layer-toggle","value":"points"});     
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
                            .attr({"class":"toggle","type":"checkbox"});
            var loader = $('<img>')
                            .attr({"src":"/static/loading-small.gif","class":"loading"})
                            .height("16px");
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
                    mol.util.log('Map handling event: ' + 
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
                                mol.eventBus.trigger(mol.event.Types.SHOW_LAYER_STACK); 
                                break;
                            case "download-error":
                                console.log('hi');
                                var error = $('<button>')
                                                .attr({"class":"error"})
                                                .html('!');
                                console.log(error);
                                $(self.row).find(".loading").replaceWith(error);
                                mol.eventBus.trigger(mol.event.Types.SHOW_LAYER_STACK); 
                                break;
                        }
                    }
                }
            );  
            
            mol.util.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
            mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, this.row); 
                
        } else {
            return this._name;
        }
    }
    if (name) this.name(name);
    
    this.source = function(source){
        self = this;
        if (source){
            this._source = source;
            switch (this._source) {
            case "GBIF":
                if (!this._name) {
                        var button = $('<button>')
                                        .attr({"id":"gbif_points_search"})
                                        .html('Go');  
                        var input = $('<input>')
                                        .attr({
                                            "type":"search",
                                            "id":"gbif_points_search_box",
                                            "value": "Puma concolor"
                                            });
                        var dialog = $('<div>')
                                        .attr({"class":"dialog list","id":"add_points_dialog"})
                                        .html('<span>Get Points From GBIF Range</span>')
                                        .append(input)
                                        .append(button);
                        $(button).click(function(){
                            if (!$(input).val()){
                                mol.util.log('No input available in: ' + $(input).attr('id'));
                            } else {
                                mol.util.log('Layer triggering event: ' + mol.event.Types.DELETE_STACK_LAYER);
                                mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, ".dialog");   
                                self.name($(input).val());
                            }
                        });
                        mol.util.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
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
 * Shows a UI for a PointsEngine.
 * 
 */
mol.engines.PointsEngine.prototype.showUi = function() {
};


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
                            .attr({"class":"toggle","type":"checkbox"});
                            
            var loader = $('<img>')
                            .attr({"src":"/static/loading-small.gif","class":"loading"})
                            .height("16px");
                            
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
                    mol.util.log('Map handling event: ' + 
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
                    }
                }
            );  
            
            mol.util.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
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
                                mol.util.log('No input available in: ' + $(input).attr('id'));
                            } else {
                                mol.util.log('Layer triggering event: ' + mol.event.Types.DELETE_STACK_LAYER);
                                mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, ".dialog");   
                                self.name($(input).val());
                            }
                        });
                        mol.util.log('Layer triggering event: ' + mol.event.Types.ADD_NEW_STACK_LAYER);
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
