/**
 * App module for running the app with a given configuration.
 */
MOL.modules.app = function(mol) {

    mol.app = {};

    mol.app.Instance = Class.extend(
        {
            init: function(config) {
                mol.log.enabled = config ? config.logging: false;
                this._control = new mol.location.Control(config);
                Backbone.history.start();
            },

            run: function() {
                mol.log.info('App is now running!');
            },
            
            getBus: function() {
                return this._control.getBus();
            }
        }
    );
};
