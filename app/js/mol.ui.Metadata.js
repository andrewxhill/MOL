
/**
 * Map module that wraps a Google Map and gives it the ability to handle app 
 * level events and perform AJAX calls to the server. It surfaces custom
 * map controls with predefined slots. 
 * 
 * Event binding:
 *     ADD_MAP_CONTROL - Adds a control to the map.
 *     ADD_LAYER - Displays the layer on the map.
 * 
 * Event triggering:
 *     None
 */
MOL.modules.Metadata = function(mol) { 
    
    mol.ui.Metadata = {};
    /**
     * The Map Engine.
     */
    mol.ui.Metadata.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constucts a new Map Engine.
             *
             * @param api the mol.ajax.Api for server communication
             * @param bus the mol.events.Bus for event handling 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;  
                this._collections = {};
            },            
            _showMetadata: function(id, colText, itemText) {
                var display = this._display,
                    self = this,
                    api = this._api,
                    ActionCallback = mol.ajax.ActionCallback,
                    LayerAction = mol.ajax.LayerAction;
                
                var par = display.find('li div');
                for (p in par){
                    par[p].removeStyleName('selected');
                }
                var itm = display.find('#'+id.replace(/\//g,"\\/"))[0];
                itm.addStyleName('selected');
                
                display.getCollectionTitle().text(colText);
                display.getItemTitle().text(itemText);
                
                var dat = display.findChild('.data');
                var mo = dat.find('.meta-object');
                for (m in mo) {
                    mo[m].removeStyleName('selected');
                }
                var meta = dat.findChild('#'+id.replace(/\//g,"\\/"))
                meta.addStyleName('selected');
                if (meta.getInnerHtml() == "") {
                    action = new LayerAction('metadata-item', {key_name:id});
                    callback = new ActionCallback(
                        function(response) {
                            self._addMetadataResult(response);
                        },

                        function(error) {
                            mol.log.error(error);
                        }
                    );
                    api.execute(action, callback);  
                }
            },
            _addMetadataResult: function(result) {
                var display = this._display,
                    dat = display.findChild('.data');
                    id = result.key_name;
                var meta = dat.findChild('#'+id.replace(/\//g,"\\/"));
                var out = result.data.source + 
                            "<br/>" + 
                            result.data.name +
                            "<br/>" + 
                            result.data.type +
                            "<br/>" ;
                meta.setInnerHtml(out);
            },
            _addDataset: function(layer) {
                var itemId = layer.getKeyName(),
                    itemName = layer.getName(),
                    collectionName = layer.getSubName(),
                    collectionId = layer.getSubName().replace(/\s/g,"_"),
                    display = this._display,
                    self = this;
                
                if (! (collectionId in this._collections)){
                    var c = display.getNewCollection(collectionId);
                    c.getName().text(collectionName);
                    
                    c.getName().click(function(e) {
                        var stE = new mol.ui.Element(e.target);
                        var id = stE.attr('id');
                        self._showMetadata(id, stE.text(), " ");
                    });
                    
                    this._collections[collectionId] = {items: {}};
                }
                    
                if (!(itemId in this._collections[collectionId].items)){
                    var it = display.getNewItem(itemId,collectionId);
                    it.getName().text(itemName);
                    it.getName().click(function(e) {
                        var stE = new mol.ui.Element(e.target);
                        var id = stE.attr('id');
                        var itm = display.find('#'+id.replace(/\//g,"\\/"))[0];
                        var col = itm.getParent().getParent().getParent();
                        colText = col.findChild('.collection').text() + ": ";
                        itemText = itm.text();
                        self._showMetadata(id,colText,itemText);
                    });
                    this._collections[collectionId].items[itemId] = 0;
                }
            },
            
            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                this._bindDisplay(new mol.ui.Metadata.Display());
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display, text) {  
                var self = this,
                    bus = this._bus,
                    LayerEvent = mol.events.LayerEvent;
                    
                this._display = display;
                display.setEngine(this);   
                
                info = {name: 'puma concolor',
                        id: 'lskdjf/dsjfl',
                        collectionName: 'wdpa',
                        getKeyName: function(){return 'lskdjf/dsjfl'},
                        getName: function(){return 'Puma concolor'},
                        getSubName: function(){return 'wdpa'},
                        
                        }
                //self._addDataset(info)
                info.getKeyName = function() {return "lsdjf/sjdfa"};
                //self._addDataset(info)
                info.getKeyName = function() {return "lsdjf/fhsk"};
                //self._addDataset(info)
                info.getKeyName = function() {return "lsdjf/ejfe"};
                //self._addDataset(info)
                
                
                bus.addHandler(
                    LayerEvent.TYPE, 
                    function(event) {
                        var action = event.getAction(),
                            layer = event.getLayer();
                        switch (action) {    
                            case 'add':
                                var layer = event.getLayer();
                                self._addDataset(layer);
                                break;
                            case 'view-metadata':
                                var colText = layer.getSubName() + ": ";
                                var itemText = layer.getName();
                                self._showMetadata(layer.getKeyName(), colText, itemText );
                                document.getElementById('metadata').scrollIntoView(true);
                            break;
                            
                        }
                    }
                );
                
            }
        }
    );

    /**
     * The Meta Object.
     */
    mol.ui.Metadata.Meta = mol.ui.Display.extend(
        {
            init: function(id) {
                this._id = id;
                this._super('<div class="meta-object" id="'+this._id+'"></div>');
            }
        }
    );
    /**
     * The Item.
     */
    mol.ui.Metadata.Item = mol.ui.Display.extend(
        {
            init: function(itemId) {
                this._id = itemId;
                this._super('<li id="container-'+this._id+'"><div id="'+this._id+'" class="item">item 1</div></li>');
            },
            getName: function() {
                var x = this._itemName,
                    s = '.item';
                return x ? x : (this._itemName = this.findChild(s));
            }
        }
    );
    /**
     * The Collection.
     */
    mol.ui.Metadata.Collection = mol.ui.Display.extend(
        {
            init: function(collectionId) {
                this._id = collectionId;
                this._super('<li id="container-' + this._id + '">' +
                        '<div id="' + this._id + '" class="collection">Collection 1</div>' +
                        '<ul class="item-list">' +
                        '</ul></li>');
            },
            getName: function() {
                var x = this._collectionName,
                    s = '.collection';
                return x ? x : (this._collectionName = this.findChild(s));
            },
            setSelected: function() {
                var s = '.collection';
                this.findChild(s).select();
            }
        }
    );
    /**
     * The Metadata Display <div> in the <body> element.
     */
    mol.ui.Metadata.Display = mol.ui.Display.extend(
        {

            /**
             * Constructs a new Metadata Display.
             * 
             * @param config the display configuration
             * @constructor
             */
            init: function(config) {
                this._id = 'metadata';
                this._super($('<div>').attr({'id': this._id}));
                $('body').append(this.getElement());
                this.setInnerHtml(this._html());
            },
            getNewCollection:  function(collectionId){
                var Collection = mol.ui.Metadata.Collection,
                    Meta = mol.ui.Metadata.Meta,
                    r = new Collection(collectionId),
                    mo = new Meta(collectionId);
                    
                this.findChild('.data').append(mo);
                this.findChild('.collection-list').append(r);
                return r;
            },
            getNewItem:  function(itemId,collectionId){
                var Item = mol.ui.Metadata.Item,
                    Meta = mol.ui.Metadata.Meta,
                    r = new Item(itemId),
                    mo = new Meta(itemId);
                this.findChild('.data').append(mo);
                c = this.findChild('#container-'+collectionId.replace(/\//g,"\\/")).findChild('.item-list').append(r);
                
                return r;
            },
            getCollectionTitle: function(){
                var x = this._collectionTitle,
                    s = '.collection-path';
                return x ? x : (this._collectionTitle = this.findChild(s));
            },
            getItemTitle: function(){
                var x = this._itemTitle,
                    s = '.item-path';
                return x ? x : (this._itemTitle = this.findChild(s));
            },
            selectItem: function(id) {
                //TODO deselect all items/collections and select the one passed by ID
            },
                    
            _html: function(){
                return  '<div class="mol-Metadata">' +
						'    <div class="top-bar">' +
						'        <a href="#map">back to map</a>' +
						'        <div class="details-menu">' +
						'            <div class="view-option selected">basic</div>' +
						'            <div class="view-option">full</div>' +
						'            <div class="title">Metadata view:</div>' +
						'        </div>' +
						'    </div>' +
						'    <div class="object-menu">' +
						'        <div class="title">Mapped data</div>' +
						'        <ul class="collection-list">' +
						'        </ul>' +
						'    </div>' +
						'    <div class="object-viewer">' +
						'        <div class="details-window">' +
						'            <div class="title">Data: <span class="collection-path"></span><span class="item-path"></span></div>' +
						'            <div class="data">' +
						'            </div>' +
						'        </div>' +
						'    </div>' +
						'</div>';
            }       
        }
    );
};
