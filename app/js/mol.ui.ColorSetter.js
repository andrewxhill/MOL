/**
 * TODO: Andrew
 */
MOL.modules.ColorSetter = function(mol) {
    
    mol.ui.ColorSetter = {};
    
    mol.ui.ColorSetter.Color = Class.extend(
        {
            init: function(r, g, b) {
                this._r = r;
                this._g = g;
                this._b = b;
            },

            getRed: function() {
                return this._r;
            },
            
            getGreen: function() {
                return this._g;                
            },

            getBlue: function() {
                return this._b;
            },

            toString: function() {
                return 'Red=' + this._r + ', Green=' + this._g +', Blue=' + this._b;                    
            }
        }
    );

    mol.ui.ColorSetter.Api = Class.extend(
        {
            /**
             * @constructor
             */
            init: function(config) {
                this._bus = config.bus;
                this._types = {};
                this._bindEvents();
            },
            
            _bindEvents: function() {
                var bus = this._bus,
                    ColorEvent = mol.events.ColorEvent;
                
                bus.addHandler(
                    ColorEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            category = event.getCategory(),
                            id = event.getId(),
                            color = null,
                            config = {
                                action: 'change',
                                color: null,
                                category: category,
                                id: id
                            };
                        
                        switch (action) {
         
                        case 'get':
                            switch (category) {
                                
                            case 'points':
                                // TODO(andrew): Logic for getting next color.
                                config.color = new mol.ui.ColorSetter.Color(32, 40, 73);
                                break;

                            case 'range':
                                config.color = new mol.ui.ColorSetter.Color(183, 42, 16);
                                break;
                            case 'ecoregion':
                                config.color = new mol.ui.ColorSetter.Color(131, 209, 6);
                                break;
                            case 'pa':
                                config.color = new mol.ui.ColorSetter.Color(255, 191, 0);
                                break;
                            }                            
                            bus.fireEvent(new ColorEvent(config));
                        }                        
                    }
                );
            }
        }
    );
};
