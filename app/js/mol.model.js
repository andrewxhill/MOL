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
            init: function(type, source, name, json) {
                this._type = type;
                this._source = source;
                this._name = name;
                this._json = json;
                this._color = null;
                this._icon = null;
                this._buildId();
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
            
            getId: function() {
                return this._id;                
            },
            
            getColor: function() {
                return this._color;                
            },
            
            setColor: function(color) {
                this._color = color;
            },
                             
            _buildId: function() {
                var type = this._type,
                    source = this._source,
                    name = this._name;
                if (this._id) {
                    return this._id;                    
                }
                this._id = [type, source, name.split(' ').join('_')].join('_');
                return this._id;
            }
        }
    );
};
