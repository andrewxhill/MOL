
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
            _showMetadata: function(id) {
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
                
                //display.getCollectionTitle().text(colText);
                //display.getItemTitle().text(itemText);
                
                var dat = display.findChild('.data');
                var mo = dat.find('.meta-object');
                for (m in mo) {
                    mo[m].removeStyleName('selected');
                }
                var meta = dat.findChild('#'+id.replace(/\//g,"\\/"))
                
                //console.log(meta.getId());
                if (meta.attr('id') != null ) {
                    meta.addStyleName('selected');
                } else {
                    var action = new LayerAction('metadata-item', {key_name:id});
                    var callback = new ActionCallback(
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
                //var meta = dat.findChild('#'+id.replace(/\//g,"\\/"));
                //meta = new this.display.Meta(itemId)
                meta = display.addNewMeta(id);
                meta.addStyleName('selected');
                
                meta.getSource().text(result.data.source + ": ");
                meta.getType().text(result.data.type);
                meta.getName().text(result.data.name);
                
                if (result.data.spatial) {
                    meta.getSpatialText().text(result.data.spatial.crs.extent.text);
                    meta.getWest().text(result.data.spatial.crs.extent.coordinates[0]);
                    meta.getSouth().text(result.data.spatial.crs.extent.coordinates[1]);
                    meta.getEast().text(result.data.spatial.crs.extent.coordinates[2]);
                    meta.getNorth().text(result.data.spatial.crs.extent.coordinates[3]);
                    var url = "/data/overview?w=256&h=128&key_name="+result.key_name;
                    console.log(url);
                    meta.overviewImg(url);
                }
                
                for (n in result.data.variables) {
                    meta.newVariable(result.data.variables[n].name,result.data.variables[n].value);
                }
                
                if (result.data.storage.location != null){
                    meta.getFileDate().text(result.data.storage.uploadDate);
                    meta.getFileLocation().text(result.data.storage.location);
                    meta.getFileFormat().text(result.data.storage.format);
                }
            },
            _itemCallback: function(e) {
                var display = this._display,
                    stE = new mol.ui.Element(e.target);
                var id = stE.attr('id');
                //var itm = display.find('#'+id.replace(/\//g,"\\/"))[0];
                //var col = itm.getParent().getParent().getParent();
                //var colText = col.findChild('.collection').text() + ": ";
                //var itemText = itm.text();
                this._showMetadata(id);
            },
            _collCallback: function(e) {
                var stE = new mol.ui.Element(e.target);
                var id = stE.attr('id');
                this._showMetadata(id, stE.text(), " ");
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
                    
                    c.getName().click( function(e) { self._collCallback(e) } );
                    
                    this._collections[collectionId] = {items: {}};
                }
                    
                if (!(itemId in this._collections[collectionId].items)){
                    var it = display.getNewItem(itemId,collectionId);
                    it.getName().text(itemName);
                    it.getName().click(function(event){self._itemCallback(event)});
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
                
                bus.addHandler(
                    LayerEvent.TYPE, 
                    function(event) {
                        var act = event.getAction();
                        switch (act) {    
                            case 'add':
                                var layer = event.getLayer();
                                self._addDataset(layer);
                                break;
                            case 'view-metadata':
                                var layer = event.getLayer();
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
                this._spatial = null;
                this._super('<div class="meta-object" id="'+this._id+'">'+
                            '   <div class="object-title">' +
                            '       <span class="src-path"></span>' +
                            '       <span class="arrow">   </span>' +
                            '       <span class="type-path"></span>' +
                            '       <h2 class="name-path"></h2>' +
                            '   </div>' +
                            '   <div class="permissions">' +
                            '       Permissions: ' +
                            '       <span class="permissions-text">unknown</span>' +
                            '   </div>' +
                            '   <div class="citation">' +
                            '       Citation: ' +
                            '       <span class="citation-text">unknown</span>' +
                            '   </div>' +
                            '   <div class="spatial"></div>' +
                            '   <div class="small-left"></div>' +
                            '</div>');
            },
            _fileInit: function() {
                this._file = new mol.ui.Element('<div class="file-data">' + 
                                    '   <div class="label">Format:</div>' + 
                                    '   <div class="file-format"></div>' + 
                                    '   <div class="label">Download:</div>' + 
                                    '   <a href="" class="file-location"></a>' + 
                                    '   <div class="label">File date:</div>' + 
                                    '   <div class="file-upload-date"></div>' + 
                                    '</div>');
                this.append(this._file);
                return this._file;
            },
            _temporalInit: function() {
                this._temporal = new mol.ui.Element('<div class="temporal">' +
                                 '   <div class="title">Temporal span:</div>' +
                                 '   <div class="start">n/a</div>' +
                                 '   <div class="bar"></div>' +
                                 '   <div class="end">n/a</div>' +
                                 '<div>');
                this.findChild('.small-left').append(this._temporal);
                return this._temporal;
            },
            _variablesInit: function() {
                this._variables = new mol.ui.Element('<div class="variables"><div class="title">Other info:</div></div>');
                this.findChild('.small-left').append(this._variables);
                return this._variables;
            },
            _spatialInit: function() {
                this._spatial = new mol.ui.Element('<div class="text">Geography: <span class="spatial-text"></span></div>' +
                                '<div class="spacolumn">' +
                                '  <div class="title">Bounding Box</div>' +
                                '  <div class="bounding-box">' +
                                '      <div class="north">90</div>' +
                                '      <div class="west">-180</div>' +
                                '      <div class="east">180</div>' +
                                '      <div class="south">-90</div>' +
                                '  </div>' +
                                '</div>' +
                                '<div class="spacolumn">' +
                                '  <div class="title">Overview</div>' +
                                '  <div class="map-overview">' +
                                '     ' +
                                '  </div>' +
                                '</div>');
                this.findChild('.spatial').append(this._spatial);
                return this._spatial;
            },
            getFileFormat: function(){
                var fi = this._file ? this._file : this._fileInit(),
                    x = this._ff,
                    s = '.file-format';
                return x ? x : (this._ff = this.findChild(s));
            },
            getFileLocation: function(){
                var fi = this._file ? this._file : this._fileInit(),
                    x = this._fl,
                    s = '.file-location';
                return x ? x : (this._fl = this.findChild(s));
            },
            getFileDate: function(){
                var fi = this._file ? this._file : this._fileInit(),
                    x = this._fu,
                    s = '.file-upload-date';
                return x ? x : (this._fu = this.findChild(s));
            },
            newVariable: function(name,value){
                var vb = this._variables ? this._variables : this._variablesInit(),
                    x = new mol.ui.Element('<div class="variable">' +
                        '    <div class="name">'+name+':</div>' +
                        '    <div class="value">'+value+'</div>' +
                        '</div>');
                this.findChild('.variables').append(x);
                return x;
            },
            overviewImg: function(src) {
                var sp = this._spatial ? this._spatial : this._spatialInit(),
                    x = this._ovimg,
                    s = '.map-overview';
                if (x) {
                    return x;
                } else {
                    this._ovimg = new mol.ui.Element('<img class="overview-img"  src="'+src+'"/>');
                    this.findChild(s).append(this._ovimg);
                    return this._ovimg;
                }
            },
            getNorth: function() {
                var sp = this._spatial ? this._spatial : this._spatialInit(),
                    x = this._north,
                    s = '.north';
                return x ? x : (this._north = this.findChild(s));
            },
            getSouth: function() {
                var sp = this._spatial ? this._spatial : this._spatialInit(),
                    x = this._south,
                    s = '.south';
                return x ? x : (this._south = this.findChild(s));
            },
            getEast: function() {
                var sp = this._spatial ? this._spatial : this._spatialInit(),
                    x = this._east,
                    s = '.east';
                return x ? x : (this._east = this.findChild(s));
            },
            getWest: function() {
                var sp = this._spatial ? this._spatial : this._spatialInit(),
                    x = this._west,
                    s = '.west';
                return x ? x : (this._west = this.findChild(s));
            },
            getSpatialText: function() {
                var sp = this._spatial ? this._spatial : this._spatialInit(),
                    x = this._sptext,
                    s = '.spatial-text';
                return x ? x : (this._sptext = this.findChild(s));
            },
            getPerms: function() {
                var x = this._perms,
                    s = '.permissions-text';
                return x ? x : (this._perms = this.findChild(s));
            },
            getSource: function() {
                var x = this._src,
                    s = '.src-path';
                return x ? x : (this._src = this.findChild(s));
            },
            getType: function() {
                var x = this._type,
                    s = '.type-path';
                return x ? x : (this._type = this.findChild(s));
            },
            getName: function() {
                var x = this._name,
                    s = '.name-path';
                return x ? x : (this._name = this.findChild(s));
            },
            
        }
    );
    /**
     * The Item.
     */
    mol.ui.Metadata.Item = mol.ui.Display.extend(
        {
            init: function(itemId) {
                this._id = itemId;
                this._super('<li id="container-'+this._id +'">' + 
                            '   <div id="'+this._id+'" class="item">item 1</div>' + 
                            '</li>');
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
                    r = new Item(itemId);
                //this.findChild('.data').append(mo);
                this.findChild('#container-'+collectionId.replace(/\//g,"\\/")).findChild('.item-list').append(r);
                return r;
            },
            addNewMeta: function(itemId) {
                var Meta = mol.ui.Metadata.Meta;
                var mo = new Meta(itemId);
                this.findChild('.data').append(mo);
                return mo;
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
						'        <a href="#map">Back to Map</a>' +
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
						'            <div class="title">Data:</div>' +
						'            <div class="data">' +
						'            </div>' +
						'        </div>' +
						'    </div>' +
						'</div>';
            }       
        }
    );
};
