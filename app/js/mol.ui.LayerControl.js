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
     * The LayerControl Engine.
     */
    mol.ui.LayerControl.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs a new engine.
             * 
             * @param api the mol.ajax.Api for server communication
             * @param bus the mol.events.Bus for event handling 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
            },

            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                var config = this._displayConfig(),
                    display = new mol.ui.LayerControl.Display(config);
                this._bindDisplay(display);
            },
            
            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('LayerControl.Engine.go()');
            },
            
            /**
             * Private function that binds the display by setting up click
             * handlers for the 'Add' and 'Delete' buttons.
             * 
             * @param display the mol.ui.LayerControl.Display object to bind 
             */
            _bindDisplay: function(display) {
                var bus = this._bus,
                    div = display.getElement()[0],
                    position = google.maps.ControlPosition.TOP_RIGHT,
                    LayerControlEvent = mol.events.LayerControlEvent,
                    MapControlEvent = mol.events.MapControlEvent;

                this._display = display;
                display.setEngine(this);                
                
                bus.fireEvent(new MapControlEvent(div, position, 'add'));

                display.getAddLink().click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('add-click'));
                    }
                );

                display.getDeleteLink().click(
                    function(event) {
                        bus.fireEvent(new LayerControlEvent('delete-click'));
                    }
                );
            },

            /**
             * Private function that returns a configuration object for the 
             * mol.ui.LayerControl.Display object.
             */
            _displayConfig: function() {
                return {
                    text: {
                        addLayer: 'Add',
                        deleteLayer: 'Delete',
                        layers: 'Layers'
                    }
                };
            }
        }
    );

    /**
     * The list menu that contains options for adding and deleting layers.
     */
    mol.ui.LayerControl.Menu = mol.ui.Element.extend(
        {
            init: function(name) {
                this._super('<ul>');
                this.setStylePrimaryName('mol-LayerControl-Menu');
                this._name = name;
                this._options = {};
                var label = new mol.ui.LayerControl.MenuOptionLabel(name);
                this._options[name] = label;
                this.append(label);
            },

            buildOptions: function(names) {
                var name = null,
                    option = null;
                for (x in names) {
                    name = names[x];
                    option = new mol.ui.LayerControl.MenuOption(name);
                    this._options[name] = option;
                    this.append(option);
                }
            },

            getOption: function(name) {
                return this._options[name];
            }
        }
    );

    /**
     * The menu option.
     */
    mol.ui.LayerControl.MenuOption = mol.ui.Element.extend(
        {
            init: function(name) {                
                this._super('<li>');
                this.setStyleName('mol-LayerControl-MenuOption');   
                this.addStyleName('mol-LayerControl-Menu');   
                this._link = new mol.ui.LayerControl.MenuOptionLink(name);
                this.getElement().append(this._link.getElement());
            },

            getLink: function() {
                return this._link;
            }
        }
    );
    
    /**
     * The menu option link.
     */
    mol.ui.LayerControl.MenuOptionLink = mol.ui.Element.extend(
        {
            init: function(name) {
                this._super('<a>');
                this.setStyleName('mol-LayerControl-MenuOptionLink');
                this.getElement().html(name);                
            }
        }
    );
    
    /**
     * The menu option label.
     */
    mol.ui.LayerControl.MenuOptionLabel = mol.ui.LayerControl.MenuOption.extend(
        {
            init: function(name) {
                this._super(name);
                this.setStyleName('mol-LayerControl-MenuOptionLabel');
                this.addStyleName('mol-LayerControl-MenuOption');   
                this.addStyleName('mol-LayerControl-Menu');   
            }
        }
    );

    /**
     * The top right map control container. It gets added to the Google map as a
     * control. 
     */
    mol.ui.LayerControl.RightController = mol.ui.Element.extend(
        {
            init: function() {
                this._super('<div>');
                this.addStyleName('mol-LayerControl-Display');
            }
        }
    );

    /**
     * The container for Layers, Filters, Tools, and other control widgets on
     * the map. Its parent is RightController.
     */
    mol.ui.LayerControl.WidgetContainer = mol.ui.Element.extend(
        {
            init: function() {
                this._super('<div>');
                this.setStyleName('mol-WidgetContainer');
            },

            setWidget: function(widget) {
                this.append(widget);
            }
        }        
    ),

            
    /**
     * The LayerControl Display.
     */
    mol.ui.LayerControl.Display = mol.ui.Display.extend(
        {
            
            /**
             * Constructs a new LayerControl Display.
             * 
             * @param config the display configuration
             * @constructor
             */            
            init: function(config) {
                this._super('<div>');
                this.setStyleName('mol-RightController');
                this._config = config;
                this._build();
            },

            /**
             * Public function that returns the 'Add' widget of this display.
             */
            getAddLink: function() {
                var name = this._config.text.addLayer;
                return this._menu.getOption(name).getLink();
            },

            /**
             * Public function that returns the 'Delete' widget of this display.
             */
            getDeleteLink: function() {
                var name = this._config.text.deleteLayer;
                return this._menu.getOption(name).getLink();
            },

            /**
             * Private function that builds the UI and attaches it to the 
             * root element of the display.
             */
            _build: function() {
                var element = this.getElement(),
                    addText = this._config.text.addLayer,
                    deleteText = this._config.text.deleteLayer,
                    layersText = this._config.text.layers,
                    names = [deleteText, addText];
                this._widgetContainer = new mol.ui.LayerControl.WidgetContainer();
                this.append(this._widgetContainer);
                this._menu = new mol.ui.LayerControl.Menu(layersText);                    
                this._menu.buildOptions(names);
                this._widgetContainer.append(this._menu);
            }
        }
    );
};
