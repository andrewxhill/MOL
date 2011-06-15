/**
 * Model module.
 */
MOL.modules.model = function(mol) {
  
    mol.model = {};

    mol.model.Model = Class.extend(
        {           
            init: function(props) {
                this._props = props;
            },

            get: function(name) {
                return this._props[name];
            },

            toJson: function() {
                return JSON.stringify(this._props);
            }
        }
    );

    mol.model.LayerSource = mol.model.Model.extend(
        {
            init: function(props) {
                this._super(props);
            },

            getId: function() {
                return this.get('id');
            },

            getNames: function() {
                return this.get('names');
            },

            getTypes: function() {
                return this._get('types');
            }
        }
    );

    /**
     * The layer model.
     */
    mol.model.Layer = Class.extend(
        {
            init: function(params) {
                this._type = params.type;
                this._source = params.source;
                this._name = params.name;
                this._name2 = params.name2;
                this._key_name = params.key_name;
                this._json = params.json;
                this._color = null;
                this._icon = null;
            },

            hasPoints: function() {
                // TODO                
            },

            hasRange: function() {
                // TODO
            },

            getIcon: function() {
                return this._icon;
            },
            
            setIcon: function(icon) {
                this._icon = icon;
            },
            
            getType: function() {
                return this._type;                
            },

            getSource: function() {
                return this._source;
            },
            
            getName: function() {
                return this._name;                
            },
            
            getSubName: function() {
                return this._name2;                
            },

            getKeyName: function() {
                return this._key_name;                
            },
            
            getId: function() {
                return this._key_name;
            },
            
            getLid: function() {
                return this._key_name.split('/',2)[2];
            },
            
            getColor: function() {
                return this._color;                
            },
            
            setColor: function(color) {
                this._color = color;
            }
        }
    );
};
