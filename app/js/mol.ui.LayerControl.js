/**
 * LayerControl module that presents a map control for adding or deleting layers. 
 * It can handle app level events and perform AJAX calls to the server.
 * 
 * Event binding:
 *     None
 * 
 * Event triggering:
 *     ADD_LAYER - Triggered when the Add widget is clicked
 *     DELETE_LAYER - Triggered when the Delete widget is clicked
 */
MOL.modules.LayerControl = function(mol) {
    
    mol.ui.LayerControl = {};
    
    /**
     * The Layer engine.
     */
    mol.ui.LayerControl.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs the engine.
             * 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
                this._layerIds = {};
            },

            /**
             * Starts the engine by creating and binding the display.
             *
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                this._bindDisplay(new mol.ui.LayerControl.Display());
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                var visible = place.lv ? parseInt(place.lv) : 0,
                    display = this._display;
                
                display.toggleLayers(visible);
            },

            getPlaceState: function() {
                return {
                    lv: this._display.isLayersVisible() ? 1 : 0,
                    layers: _.keys(this._layerIds).join(',')
                };
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display, text) {                
                var self = this,
                    LayerControlEvent = mol.events.LayerControlEvent,
                    LayerEvent = mol.events.LayerEvent,
                    widget = null,
                    bus = this._bus, 
                    ch = null,
                    styles = null,
                    layerId = null;


                this._display = display;
                display.setEngine(this);            
                
                // Clicking the layer button toggles the layer stack:
                widget = display.getLayerToggle();
                widget.click(
                    function(event) {
                        display.toggleLayers();
                    }
                );
                
                // Clicking the share button gets the shareable URL for the current view:
                widget = display.getShareButton();
                widget.click(
                    function(event) {
                        bus.fireEvent(new MOL.env.events.LocationEvent({}, 'get-url'));
                    }
                );
                
                bus.addHandler(
                  "LocationEvent", 
                  function(event){
                    if (event.getAction() == 'take-url') {
                        display.toggleShareLink(event.getLocation().url);
                    }
                  }
                );                
                
                // Clicking the add button fires a LayerControlEvent:
                widget = display.getAddButton();
                widget.click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('add-click'));
                        display.toggleShareLink("", false);
                    }
                );
                
                // Clicking the delete button fires a LayerControlEvent:
                widget = display.getDeleteButton();
                widget.click(
                    function(event) {
                        ch = new mol.ui.Element($('.layer.widgetTheme.selected')[0]);
                        layerId = ch.attr('id');
                        ch.remove();
                        bus.fireEvent(new LayerControlEvent('delete-click', layerId));
                        delete self._layerIds[layerId];
                        self._display.toggleShareLink("", false);
                    }
                );
                
                this._addDisplayToMap();
                
                bus.addHandler(
                    LayerEvent.TYPE, 
                    function(event) {
                        var action = event.getAction(),
                            layer = event.getLayer(),
                            layerId = layer.getKeyName(),
                            layerType = layer.getType(),
                            layerName = layer.getName(),
                            layerSubName = layer.getSubName(),
                            layerIds = self._layerIds,
                            layerUi = null,
                            display = self._display,
                            LayerEvent = mol.events.LayerEvent,
                            ch = null,
                            widget = null,
                            nullTest = null,
                            styleNames = null;
                    
                        switch (action) {                                                       
    
                        case 'add':
                            if (layerIds[layerId]) {
                                // Duplicate layer.
                                return;
                            }
                            display.toggleLayers(true);
                            display.toggleShareLink("", false);
                            layerIds[layerId] = true;
                            layerUi = display.getNewLayer();
                            layerUi.getName().text(layerName);
                            layerUi.getType().attr("src","/static/maps/search/"+ layerType +".png");
                            layerUi.attr('id', layerId);
                            
                            
                            var ntst = function() {
                                var f = "/static/config/nulltest.js"; 
                                var s = document.createElement('script'); 
                                s.setAttribute("type","text/javascript"); 
                                s.setAttribute("src", f); 
                                document.getElementsByTagName("head")[0].appendChild(s);
                            };
                            nullTest = (layerId == 'points/gbif/13816451') ? ntst() : function(){};

                            
                            layerUi.click(function(e) {
                                ch = new mol.ui.Element(e.target).getParent().findChildren('.layer');
                                for (y in ch) {
                                    styleNames = ch[y].getStyleName().split(' ');
                                    if (_.indexOf(styleNames, 'selected') > -1) {
                                        ch[y].removeStyleName('selected');    
                                        return;
                                    }                                    
                                }
                                new mol.ui.Element(e.target).addStyleName('selected');
                            });
                            
                            widget = layerUi.getToggle();
                            widget.setChecked(true);
                            widget.click(
                                function(event) {
                                    console.log(widget);
                                    bus.fireEvent(
                                        new LayerEvent(
                                            {
                                                action: widget.isChecked() ? 'checked': 'unchecked',
                                                layer: layer
                                            }
                                        )
                                    );
                                }
                            );
                            break;
                        }
                    }
                );
            },

            /**
             * Fires a MapControlEvent so that the display is attached to
             * the map as a control in the TOP_LEFT position.
             */
            _addDisplayToMap: function() {
                var MapControlEvent = mol.events.MapControlEvent,
                    display = this._display,
                    bus = this._bus,
                    DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    ControlPosition = mol.ui.Map.Control.ControlPosition,
                    action = 'add',
                    config = {
                        display: display,
                        action: action,
                        displayPosition: DisplayPosition.TOP,
                        controlPosition: ControlPosition.TOP_RIGHT
                    };
                bus.fireEvent(new MapControlEvent(config));     
            }
        }
    );
    
    mol.ui.LayerControl.Layer = mol.ui.Display.extend(
        {
            init: function() {
                this._super(this._html());
            },

            getName: function() {
                var x = this._layerName,
                    s = '.layerNomial';
                return x ? x : (this._layerName = this.findChild(s));
            },  
            getSubName: function() {
                var x = this._layerSubName,
                    s = '.layerAuthor';
                return x ? x : (this._layerSubName = this.findChild(s));
            }, 
            getToggle: function() {
                var x = this._layerToggle,
                    s = '.toggle';
                return x ? x : (this._layerToggle = this.findChild(s));
            },  
            getType: function() {
                var x = this._layerType,
                    s = '.type';
                return x ? x : (this._layerType = this.findChild(s));
            },  
            getInfoLink: function() {
                var x = this._layerInfoLink,
                    s = '.info';
                return x ? x : (this._layerInfoLink = this.findChild(s));
            },  

            _html: function() {
                return  '<div class="layer widgetTheme">' +
                        '    <button><img class="type" src="/static/maps/search/points.png"></button>' +
                        '    <div class="layerName">' +
                        '        <div class="layerNomial">Smilisca puma</div>' +
                        '    </div>' +
                        '    <div class="buttonContainer">' +
                        '        <input class="toggle" type="checkbox">' +
                        '        <span class="customCheck"></span> ' +
                        '    </div>' +
                        '    <button class="info">i</button>' +
                        '</div>';
            }
        }
    );
    
    /**
     * The LayerControl display.
     */
    mol.ui.LayerControl.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super();
                this.setInnerHtml(this._html());
                this._config = config;
                this._show = false;
                this._shareLink = false;
            },     
            getLayerToggle: function() {
                var x = this._layersToggle,
                    s = '.label';
                return x ? x : (this._layersToggle = this.findChild(s));
            },    
            getAddButton: function() {
                var x = this._addButton,
                    s = '.add';
                return x ? x : (this._addButton = this.findChild(s));
            },  
            getDeleteButton: function() {
                var x = this._deleteButton,
                    s = '.delete';
                return x ? x : (this._deleteButton = this.findChild(s));
            },
            getShareButton: function() {
                var x = this._shareButton,
                    s = '.share';
                return x ? x : (this._shareButton = this.findChild(s));
            },
            
            getNewLayer: function(){
                var Layer = mol.ui.LayerControl.Layer,
                    r = new Layer();
                this.findChild('.scrollContainer').append(r);
                return r;
            },      
            
            isLayersVisible: function() {
                return this._show;
            },

            toggleShareLink: function(url, status) {
                var r = this._linkContainer,
                    p = '.staticLink',
                    u = '.link';
                this._url = url;
                if ( ! r ){
                    r = this.findChild(p);
                    this._linkContainer = r;
                }
                if (status == false) {
                    r.hide();
                    this._shareLink = false;
                } else if (status==true) {
                    r.show();
                    this._shareLink = true;
                } else {
                    if (this._shareLink ) {  
                        r.hide();
                        this._shareLink = false;
                    } else {
                        r.show();
                        this._shareLink = true;
                    }
                }
                this.findChild('.linkText').val(url);
                this.findChild('.linkText').select();
                
            },
            
            toggleLayers: function(status) {
                var x = this._toggleLayerImg,
                    c = this._layerContainer,
                    s = '.layersToggle',
                    n = '.scrollContainer';
                if ( ! x ){
                    x = this.findChild(s);
                    this._toggleLayerImg = x;
                }
                if ( ! c ){
                    c = this.findChild(n);
                    this._layerContainer = c;
                }
                if (this._show != status) {
                    if (this._show ) {  
                        c.hide();
                        x.attr("src","/static/maps/layers/expand.png");
                        this._show = false;
                    } else {
                        c.show();
                        x.attr("src","/static/maps/layers/collapse.png");
                        this._show = true;
                    }
                }
            },
                    
            _html: function(){
                return  '<div class="mol-LayerControl-Menu ">' +
                        '    <div class="label">' +
                        '       <img class="layersToggle" src="/static/maps/layers/expand.png">' +
                        '    </div>' +
                        '    <div class="widgetTheme share button">Share</div>' +
                        '    <div class="widgetTheme delete button">Delete</div>' +
                        '    <div class="widgetTheme add button">Add</div>' +
                        '</div>' +
                        '<div class="mol-LayerControl-Layers">' +
                        '      <div class="staticLink widgetTheme" >' +
                        '          <input type="text" class="linkText" />' +
                        '      </div>' +
                        '   <div class="scrollContainer">' +
                        '   </div>' +
                        '</div>';
            }
        }
    );
};
