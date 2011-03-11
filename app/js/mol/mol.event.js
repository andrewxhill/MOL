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
