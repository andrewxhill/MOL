// =============================================================================
// LayerStack object

/**
 * Constructor for a LayerStack.
 * 
 * @constructor
 */
mol.ui.LayerStack = function(context) {
    this.context = context;
    this.buildUi();
    this.wireEvents();        
    mol.eventBus.trigger(
        mol.event.Types.ADD_CUSTOM_MAP_CONTROL,
        this.container, 
        google.maps.ControlPosition.TOP_RIGHT
    );               
};

/**
 * Builds the UI for a LayerStack.
 */
mol.ui.LayerStack.prototype.buildUi = function() {
    this.options = $('<ul>').attr({'class': 'options list'});
    this.addLayer = $('<a>').attr(
        {'id': 'add_layer', 'href':'javascript:'});
    this.addLayer.html('Add');
    this.deleteLayer = $('<a>').attr(
        {'id': 'delete_layer', 'href':'javascript:'});
    this.deleteLayer.html('Delete');
    this.id = 'widget-container';
    this.container = $('<div>').attr({'id':'widget-container'}),
    this.layers = $('<div>').attr({'id':'layers'}),
    this.menu = $('<div>').attr({'id':'menu'}),
    this.list = $('<div>').attr({'id':'list'}),
    $(this.options).append($('<li>').attr({'class':'option list','id':'add'}));
    $(this.options).append(this.addLayer);
    $(this.options).append($('<li>').attr({'class':'option list','id':'delete'}));
    $(this.options).append(this.deleteLayer);        
    $(this.menu).append(this.options);
    $(this.layers).append(this.menu);
    $(this.layers).append(this.list);
    $(this.container).append(this.layers);
};

/**
 * Wires UI events and EventBus events for a LayerStack.
 */
mol.ui.LayerStack.prototype.wireEvents = function() {    
    var self = this;
    // Wires event for clicking the delete layer button:
    $(this.deleteLayer).click(
        function() {
            var id = $("#layers .layer.list input:checked");
            mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, id);
        }
    );
    // Wires the event for clicking the add layer button:
    $(this.addLayer).click(
        function() {
            var layer = new mol.maps.Layer({});
            // TODO: Trigger event?
        }
    );
    // Wires an event handler for when a new layer is added to stack:
    mol.eventBus.bind(
        mol.event.Types.ADD_NEW_STACK_LAYER,
        function(layerUI) {
            $(self.list).prepend($(layerUI));
        }
    );    
};