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
        'right-controller',
        true
    );               
};

/**
 * Handles tray minimizing for stack.
 * 
 */
mol.ui.Focus = function() {
    this.controllers = {};
    /* SETUP HIDING FOR THE STACK*/
    var self = this;
    this.setStackFocus = function(divId,focus,fromUI){
        var _self = this;
        if (focus) {
            self.controllers[divId].timeout = 1;
            /* show */
            $("#"+divId+" #menu .option").show('slow');
            $("#"+divId+" #list").show('slow');
        } else {
            if (fromUI){
                self.controllers[divId].timeout = 0;
                setTimeout(function(){
                    mol.eventBus.trigger(
                        mol.event.Types.CONTROLLER_FOCUS_UPDATE,
                        divId, 
                        false
                    );   
                 }, 2500);
            } else if (self.controllers[divId].timeout == 0){
                /* hide */
                var hide = true;
                for (c in self.controllers){
                    if(self.controllers[c].timeout==1){
                        hide=false;
                    }
                }
                if (hide) {
                    $("#"+divId+"  #menu .option:not(#menuLabel)").hide('slow');
                    $("#"+divId+"  #list").hide('slow');
                } else {
                    setTimeout(function(){
                        mol.eventBus.trigger(
                            mol.event.Types.CONTROLLER_FOCUS_UPDATE,
                            divId, 
                            false
                        );   
                     }, 500);
                }
            }
        }
    }
    mol.eventBus.bind(
        mol.event.Types.CONTROLLER_FOCUS_UPDATE, 
        function(divId, focus, fromUI) {
            if (!self.controllers[divId]) {
                self.controllers[divId] = {'timeout': 1};
            }
            self.setStackFocus(divId,focus,fromUI);
        }
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
    
    this.id = 'layer-widget-container';
    this.container = $('<div>').attr({'id':'layer-widget-container','class':'widget-container'}),
    this.layers = $('<div>').attr({'id':'layers'}),
    this.menu = $('<div>').attr({'id':'menu'}),
    this.list = $('<div>').attr({'id':'list'}),
    $(this.options).append(
        $('<li>').attr({'class':'option list','id':'menuLabel'}
                      ).html('Layers'));  
    $(this.options).append(
        $('<li>').attr({'class':'option list','id':'delete'}
                      ).append(this.deleteLayer)); 
    $(this.options).append(
        $('<li>').attr({'class':'option list','id':'add'}
                      ).append(this.addLayer));
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
                if ($(layerUI).attr('class') == 'layer'){
                    /* TELL THE LAYER TO REMOVE ITSELF */
                } else {
                    mol.log('LayerStack handling event: ' + 
                                mol.event.Types.ADD_NEW_STACK_LAYER + ': removed an existing stack layer');
                    $("#layers #"+$(layerUI).attr('id')).remove();
                }
            } else {
                if ("dialog" == $(layerUI).attr('class').split(' ')[0]){
                    /*avoid dialog stacking */
                    $("#layers .dialog").remove();
                }
                mol.log('LayerStack handling event: ' + 
                             mol.event.Types.ADD_NEW_STACK_LAYER);
                $(self.list).prepend($(layerUI));
                if ($(self.list).find('.layer').length == 1){
                    $(layerUI).find("input[name=active-layer]").click();
                }
            }
        }
    );    
};
