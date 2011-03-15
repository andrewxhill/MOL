/**
 * Constructor for the Layer object.
 * 
 * @param options An object that contains options for type, source, name, data
 * @constructor
 */
mol.maps.Layer = function(options) {  
    this.type = options.type;
    this.source = options.source;
    this.name = options.name;
    this.data = options.data;
    if (this.type) {        
        this.build();
        return;
    } 
    this.showTypesUi();
};

/**
 * Builds the layer by selecting an engine and source.
 */
mol.maps.Layer.prototype.build = function() {
    switch (this.type) {
    case "points":
        this.engine = new engine().Points();
        if (!this.source) {
            //for the future when more soruces are available
            this.engine.setSource('gbif');
        } else {
            this.engine.setSource(this.source);
        }
        break;
    case "range":
        this.engine = new engine().Range();
        if (!this.source){
            //for the future when more soruces are available
            this.engine.setSource('mol');
        } else {
            this.engine.setSource(this.source);
        }
        break;
    }
};

/**
 * Shows the types UI.
 */
mol.maps.Layer.prototype.showTypesUi = function() {
  var dialog = null,
      buttonPoints = null,
      buttonRange = null,
      self = this;
    dialog = $('<div class="dialog list" id="add_new_layer_dialog">');
    buttonPoints = $('<button>').attr(
        {"id":"add_points_button","class":"dialog_buttons"});
    buttonPoints.html('Add Points');
    $(dialog).append(buttonPoints);
    buttonRange = $('<button>').attr(
        {"id":"add_range_button","class":"dialog_buttons"});
    buttonRange.html('Add Range Map');
    $(dialog).append(buttonRange);    
    $(buttonPoints).click(
        function() {
            self.type = 'points';
            self.build();
        }
    );
    $(buttonRange).click(
        function() {
            self.type = 'range';
            self.build();
        }
    );        
   mol.eventBus.trigger(mol.event.Types.ADD_NEW_STACK_LAYER, dialog);                                         
};

