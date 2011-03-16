// =============================================================================
// LayerStack object

/**
 * Constructor for a LayerStack.
 * 
 * @constructor
 * 
 */
mol.ui.LayerStack = function(context) {
    this.context = context;
    this.stackFocus = 0;
    this.buildUi();
    this.wireEvents();          
    mol.log('LayerStack triggering event: ' + 
                 mol.event.Types.ADD_CUSTOM_MAP_CONTROL);
    mol.eventBus.trigger(
        mol.event.Types.ADD_CUSTOM_MAP_CONTROL,
        this.container, 
        google.maps.ControlPosition.TOP_RIGHT
    );               
};

/**
 * Builds the UI for a LayerStack.
 * 
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
    $(this.options).append(
        $('<li>').attr({'class':'option list','id':'delete'}
                      ).append(this.deleteLayer)); 
    $(this.options).append(
        $('<li>').attr({'class':'option list','id':'add'}
                      ).append(this.addLayer));
    $(this.options).append(
        $('<li>').attr({'class':'option list','id':'menuLabel'}
                      ).html('Layers'));  
    $(this.menu).append(this.options);
    $(this.layers).append(this.menu);
    $(this.layers).append(this.list);
    $(this.container).append(this.layers);
    
    /* SETUP SORTABLE LAYER STACK */
    $(this.list).sortable(
        { 
            items: '.layer',
            cursor: 'move'
        }
    );
    $(this.list).disableSelection();
    
    
    /* SETUP HIDING FOR THE STACK*/
    var self = this;
    this.setStackFocus = function(focus,fromUI){
        var _self = this;
        if (focus) {
            _self.timeout = 1;
            /* show */
            $("#widget-container #list").show('slow');
        } else {
            if (fromUI){
                _self.timeout = 0;
                setTimeout(function(){
                    self.setStackFocus(false);
                 }, 5000);
            } else if (_self.timeout == 0){
                /* hide */
                $("#widget-container #list").hide('slow');
            }
        }
    }
    $(this.container).mouseover(function(){
        self.setStackFocus(true);
    });
    $(this.container).mouseleave(function(){
        self.setStackFocus(false,true);
    });
    mol.eventBus.bind(
        mol.event.Types.SHOW_LAYER_STACK, 
        function() {
            self.setStackFocus(true);
            self.setStackFocus(false,true);
        }
    );
};

/**
 * Wires UI events and EventBus events for a LayerStack.
 * 
 */
mol.ui.LayerStack.prototype.wireEvents = function() {    
    var self = this;
    // Wires event for clicking the delete layer button:
    $(this.deleteLayer).click(
        function() {
            mol.log('LayerStack.deleteLayer.click');
            var id = $("#layers .layer.list input:checked");
            mol.eventBus.trigger(mol.event.Types.DELETE_STACK_LAYER, id);
        }
    );
    // Wires the event for clicking the add layer button:
    $(this.addLayer).click(
        function() {
            if ($("#layers").find("#add_new_layer_dialog").length > 0){
                mol.log('LayerStack.addLayer.click:' +
                                'removed existing dialog');
                $("#layers #add_new_layer_dialog").remove();
            } else {
                mol.log('LayerStack.addLayer.click');
                var layer = new mol.maps.Layer();
                // TODO: Trigger event?
            }
        }
    );
    // Wires an event handler for when a class needs to remove a layer from stack:
    mol.eventBus.bind(
        mol.event.Types.DELETE_STACK_LAYER,
        function(layerIdentifier) {
            if ($(self.list).find(layerIdentifier).length > 0){
                mol.log('LayerStack handling event: ' + 
                             mol.event.Types.DELETE_STACK_LAYER +
                             ': removed an existing stack layer');
                $("#layers "+layerIdentifier).remove();
            } else {
                mol.log('LayerStack handling event: ' + 
                             mol.event.Types.DELETE_STACK_LAYER +
                             ': layer did not exist');
            }
        }
    );   
    // Wires an event handler for when a new layer is added to stack:
    mol.eventBus.bind(
        mol.event.Types.ADD_NEW_STACK_LAYER,
        function(layerUI) {
            if ($(self.list).find("#"+$(layerUI).attr('id')).length > 0){
                mol.log('LayerStack handling event: ' + 
                             mol.event.Types.ADD_NEW_STACK_LAYER +
                             ': removed an existing stack layer');
                $("#layers #"+$(layerUI).attr('id')).remove();
            } else {
                if ("dialog" == $(layerUI).attr('class').split(' ')[0]){
                    /*avoid dialog stacking */
                    $("#layers .dialog").remove();
                }
                mol.log('LayerStack handling event: ' + 
                             mol.event.Types.ADD_NEW_STACK_LAYER);
                $(self.list).prepend($(layerUI));
            }
        }
    );    
};
