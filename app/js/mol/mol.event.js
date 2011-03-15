/**
 * The event bus.
 *
 * @constructor
 */
mol.event.EventBus = function() {
    if (!(this instanceof mol.event.EventBus)) {
        return new mol.event.EventBus();
    }
    _.extend(this, Backbone.Events);
    return this;
};

mol.event.Types = {
    ADD_CUSTOM_MAP_CONTROL: 'add-custom-map-controller',
    ADD_NEW_MAP_LAYER: 'add-new-map-layer',
    REORDER_MAP_LAYERS: 'reorder-map-layers',
    ADD_NEW_STACK_LAYER: 'add-new-stack-layer',
    DELETE_STACK_LAYER: 'delete-stack-layer'
};
