/**
 * AJAX module for communicating with the server. Contains an Api object that 
 * can be used to execute requests paired with success and failure callbacks.
 */
MOL.modules.ajax = function(mol) {
    mol.ajax = {};
    
    /**
     * Action.
     */
    mol.ajax.Action = Class.extend(
        {
            init: function(name, type, params) {
                this.name = name;
                this.type = type;
                this.params = params || {};
            },
            
            toJson: function() {
                return JSON.stringify(this);
            },

            getName: function() {
                return this.name;
            },
            
            getType: function() {
                return this.type;
            },

            getParams: function() {
                return this.params;
            }
        }
    );

    /**
     * ActionCallback.
     */
    mol.ajax.ActionCallback = Class.extend(
        {
            init: function(success, failure) {
                this._success = success;
                this._failure = failure;
            },

            /**
             * @param error - the mol.exceptions.Error that caused failure
             */
            onFailure: function(error) {
                this._failure(error);
            },
            
            /**
             * @param actionResponse - the mol.ajax.ActionResponse for the action
             */
            onSuccess: function(actionResponse) {
                this._success(actionResponse);
            }
        }
    );

    
    /**
     * The layer action.
     */
    mol.ajax.LayerAction = mol.ajax.Action.extend(
        {
            /**
             * @param type - the action type (only 'search' for now)
             */
            init: function(type, params) {
                console.log(type);
                console.log(params);
                this._super('LayerAction', type, params);                
            }
        }
    );
    


    /**
     * The AJAX API.
     */
    mol.ajax.Api = Class.extend(
        {
            /**
             * Constructs a new Api object with an event bus.
             * 
             * @param bus mol.events.Bus
             * @constructor
             */
            init: function(bus) {
                this._bus = bus;
            },
            
            /**
             * Executes an action asynchronously.
             * 
             * @param action the mol.ajax.Action
             * @param callback the mol.ajax. ActionCallback
             */
            execute: function(action, callback ) {
                var params = {action: action.toJson()},
                    xhr = $.post('/webapp', params, 'json'),
                    self = this;

                xhr.success(
                    function(response) {
                        callback.onSuccess(response);
                        self.fireEvents(action);
                    }
                );

                xhr.error(
                    function(error) {
                        callback.onFailure(error);
                    }
                );
            },

            fireEvents: function(action) {
                var bus = this._bus,
                    actionName = action.getName(),
                    actionType = action.getType();

                switch (actionName) {

                case 'LayerAction':
                    switch (actionType) {

                    case 'search':
                        mol.log.todo('Fire LayerEvent');                        
                    }
                }                        
            }
        }
    );    
};

