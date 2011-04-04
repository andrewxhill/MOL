mol = MOL(function(mol){return mol;});

var r =  mol.ajax.ActionResponse.extend(
        {
            getLayers: function(name, source, type, profile) {
                var response = this._response,
                    currentProfile = profile ? profile : 'nameProfile',
                    nameProfile = name ? response.names[name] : null,
                    sourceProfile = source ? response.sources[source] : null,
                    typeProfile = type ? response.types[type] : null,
                    profileSatisfied = false;
                
                switch (currentProfile) {
                    
                case 'nameProfile':
                    if (!name) {
                        return this.getLayers(name, source, type, 'sourceProfile');
                    }

                    // See if nameProfile satisfies source and type constraints:
                    if (nameProfile) {                        
                        
                        if (!source && !type) {
                            return nameProfile.layers;
                        } 
                        
                        if (source && type) {
                            if (_.indexOf(nameProfile.sources, source) &&
                                _.indexOf(nameProfile.types, type)) {
                                return _.intersect(
                                    nameProfile.layers, 
                                    this.getLayers(name, source, type, 'sourceProfile'));
                            }
                        } 

                        if (source && !type) {
                            if (_.indexOf(nameProfile.sources, source)) {
                                return _.intersect(
                                   nameProfile.layers, 
                                   this.getLayers(name, source, type, 'sourceProfile'));
                            }
                        } 

                        if (!source && type) {
                            if (_.indexOf(nameProfile.types, type)) {
                                return _.intersect(
                                    nameProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));
                            }
                        }                            
                    } 
                    return [];                        
                    
                case 'sourceProfile':
                    if (!source) {
                        return this.getLayers(name, source, type, 'typeProfile');
                    }
                    
                    // See if sourceProfile satisfies name and type constraints:
                    if (sourceProfile) {
                        
                        if (!name && !type) {
                            return sourceProfile.layers;
                        } 
                        
                        if (name && type) {
                            if (_.indexOf(sourceProfile.names, name) &&
                                _.indexOf(sourceProfile.types, type)) {
                                return _.intersect(
                                    sourceProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));                                
                            }    
                        }
                        
                        if (name && !type) {
                            if (_.indexOf(sourceProfile.names, name)) {
                                return sourceProfile.layers;
                            }
                        } 
                        
                        if (!name && type) {
                            if (_.indexOf(sourceProfile.types, type)) {
                                return _.intersect(
                                    sourceProfile.layers, 
                                    this.getLayers(name, source, type, 'typeProfile'));                                
                            }
                        }                        
                    } 

                    return [];

                case 'typeProfile':
                    if (!type) {
                        return [];
                    }
                    
                    // See if type Profile satisfies name and source constraints:
                    if (typeProfile) {

                        if (!name && !source) {
                            return typeProfile.layers;
                        }
                     
                        if (name && source) {
                            if ( _.indexOf(typeProfile.names, name) &&
                                 _.indexOf(typeProfile.sources, source)) {
                                return typeProfile.layers;
                            }                            
                        } 
                        
                        if (name && !source) {
                            if (_.indexOf(typeProfile.names, name)) {
                                return typeProfile.layers;
                            }                            
                        } 
                        
                        if (!name && source) {
                            if (_.indexOf(typeProfile.sources, source)) {
                                return typeProfile.layers;
                            }                            
                        }                        
                    }
                    
                    return [];
                } 
                
                // Invalid profile type:
                return [];
            },

            // getLayers: function(name, source, type) {
            //     var response = this._response,
            //         nameLayers = name ? response.names[name].layers : null,
            //         sourceLayers = source ? response.sources[source].layers : null,
            //         typeLayers = type ? response.types[type].layers : null,
            //         layers = [];
                
            //     if (name && source && type) {
            //         layers = _.intersect(nameLayers, sourceLayers, typeLayers);
            //     } else if (name && !source && !type) {
            //         layers = nameLayers;
            //     } else if (name && source && !type) {
            //         layers = _.intersect(nameLayers, sourceLayers);
            //     } else if (name && !source && type) {
            //         layers = _.intersect(nameLayers, typeLayers);          
            //     } else if (!name && source && !type) {
            //         layers = sourceLayers;
            //     } else if (!name && source && type) {
            //         layers = _.intersect(sourceLayers, typeLayers);          
            //     } else if (!name && !source && type) {
            //         layers = typeLayers;
            //     }
            //     return layers;
            // },

            getLayer: function(layer) {
                return this._response.layers[layer];
            },
            
            getTypeKeys: function() {
                var x = this._typeKeys,
                    types = this._response.types;
                return x ? x : (this._typeKeys = this._getKeys(types));                
            },

            getType: function(type) {
                return this._response.types[type];
            },

            getSourceKeys: function() {
                var x = this._sourceKeys,
                    sources = this._response.sources;
                return x ? x : (this._sourceKeys = this._getKeys(sources));
            },
            
            getSource: function(source) {
                return this._response.sources[source];
            },
            
            getNameKeys: function() {
                var x = this._nameKeys,
                    names = this._response.names;
                return x ? x : (this._nameKeys = this._getKeys(names));
            },

            getName: function(name) {
                return this._response.names[name];
            },

            _getKeys: function(obj){
                var keys = [];
                for(var key in obj){
                    keys.push(key);
                }
                return keys;
            }
        }
    );

var x = {    
    "query": {
        "search": "Puma",
        "offset": 0,
        "limit": 10,
        "source": null,
        "type": null,
        "advancedOption1": "foo",
        "advancedOption2": "bar"
    },

    "types": {
        "points": {
            "names": ["Puma concolor"],
            "sources": ["GBIF"],
            "layers": ["Puma concolor"]
        },
        "range": {
            "names": ["Puma concolor","Puma yagouaroundi", "Smilisca puma"],
            "sources": ["MOL"],
            "layers": ["Puma concolor","Puma yagouaroundi", "Smilisca puma"]
        }        
    },
    
    "sources": {
        "GBIF": {
            "names": ["Puma concolor"],
            "types": ["points"],
            "layers": ["Puma concolor"]
        },        
        "MOL": {
            "names": ["Puma concolor", "Puma yagouaroundi", "Smilisca puma"],
            "types": ["range"],
            "layers": ["Puma concolor", "Puma yagouaroundi", "Smilisca puma"]
        }
    },

    "names": {
        "Puma concolor": {
            "sources": ["GBIF", "MOL"],
            "layers": ["Puma concolor", "Puma yagouaroundi", "Smilisca puma"],
            "types": ["points", "range"]
        },
        "Puma yagouaroundi": {
            "sources": ["MOL"],
            "layers": ["Puma yagouaroundi"],
            "types": ["range"]            
        },    
        "Puma Smilisca": {
            "sources": ["MOL"],
            "layers": ["Smilisca puma"],
            "types": ["range"]
        }
    },

    "layers": {
        "Puma concolor": {
            "source": "GBIF",
            "type": "points",
            "otherStuff": "blah blah"
        },                
        "Puma yagouaroundi": {
            "source": "MOL",
            "type": "range",
            "otherStuff": "blah blah"
        },       
        "Puma Smilisca": {
            "source": "MOL",
            "type": "range",
            "otherStuff": "blah blah"
        }    
    }
}

json = JSON.parse(x)

var action = new mol.ajax.LayerAction('search', {q:'puma'});

var foo = new r(action, json);

