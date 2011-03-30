/**
 * Search module has a display used as a map control. It allows users to search
 * for layers to add to the map.
 */
MOL.modules.Search = function(mol) {
    
    mol.ui.Search = {};

    /**
     * The search engine.
     */
    mol.ui.Search.Engine = mol.ui.Engine.extend(
        {
            /**
             * Constructs the engine.
             * 
             * @constructor
             */
            init: function(api, bus) {
                this._api = api;
                this._bus = bus;
            },

            /**
             * Starts the engine by creating and binding the display.
             *
             * @override mol.ui.Engine.start
             */
            start: function(container) {
                //this._bindDisplay(new mol.ui.Search.Display({}));
                this._bindDisplay(container);
            },

            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @override mol.ui.Engine.go
             */
            go: function(place) {
                mol.log.todo('Search.Engine.go()');
            },
             
            /**
             * Binds the display.
             */
            _bindDisplay: function(display) {                
                var config = {
                    text : {
                        restart: 'restart',
                        close: 'close', 
                        select: 'Select',
                        range: 'Range',
                        points: 'Points',
                        types: ['GBIF', 'MOL'],
                        go: 'Go',
                        searching: 'Searching',
                        info: 'more info',
                        next: 'Next Page',
                        add: 'Add'
                    }
                };

                this._display = display;
                display.setEngine(this);

                display.hide();

                this._addLayerControlEventHandler();                
                
               
                display.getRestartButton().click(
                    function(event) {
                        mol.log.info('Search.Display.RestartButton.click()');
                    }
                );
  
                // dispaly.getCloseButton().click(
                //     function(event) {
                //         mol.log.info('Search.Display.CloseButton.click()');
                //     }
                // );
  
                // display.getSelectRangeButton().click(
                //     function(event) {
                //         mol.log.info('Search.Display.RangeButton.click()');
                //     }
                // );
  
                // display.getSelectPointsButton().click(
                //     function(event) {
                //         mol.log.info('Search.Display.SelectPointsButton.click()');
                //     }
                // );
  
                // display.getTypeSelectBox().change(
                //     function(event) {
                //         var selection = display.getTypeSelectBox().val();
                //         mol.log.info('Search.Display.TypeSelectBox.change() - ' + selection);
                //     }
                // );

                // display.getTypeSelectBox().click(
                //     function(event) {
                //         mol.log.info('Search.Display.CloseButton.click()');
                //     }
                // );
  
                // display.getSearchBox().click(
                //     function(event) {
                //         mol.log.info('Search.Display.SearchBox.click()');
                        
                //     }
                // );
  
                // display.getGoButton().click(
                //     function(event) {
                //         var query = display.getSearchBox().getText();
                //         mol.log.info('Search.Display.GoButton.click() with search: ' + query);                       
                //     }
                // );

                // display.getSearchWidget();

                this._addDisplayToMap();
            },
            
            /**
             * Fires a MapControlEvent so that the display is attached to
             * the map as a control in the TOP_LEFT position.
             */
            _addDisplayToMap: function() {
                var MapControlEvent = mol.events.MapControlEvent,
                    div = this._display.getElement()[0],
                    position = google.maps.ControlPosition.TOP_CENTER,
                    action = 'add';
                bus.fireEvent(new MapControlEvent(div, position, action));     
            },

            /**
             * Adds an event handler for LayerControlEvent events so that a
             * 'add-click' action will show the search display as a control
             * on the map.
             */
            _addLayerControlEventHandler: function() {
                var display = this._display,
                    bus = this._bus,
                    LayerControlEvent = mol.events.LayerControlEvent;
                
                bus.addHandler(
                    LayerControlEvent.TYPE,
                    function(event) {
                        var action = event.getAction(),
                            displayNotVisible = !display.isVisible();               
                        
                        if (action === 'add-click' && displayNotVisible) {
                            display.show();
                        }
                    }
                );
            }
        }
    );

    /**
     * Mock search display for testing engine
     */
    mol.ui.Search.MockDisplay = mol.ui.Display.extend(
        {
            restartButton: {
                click: function(handler) {
                    this.restartButtonClickHandler = handler;
                },
                
                test: function() {
                    this.restartButtonClickHandler();
                }
            },
            
            getRestartButton: function() {
                return this.restartButton;
            }
        }
    );
    
    /**
     * The search display.
     */
    mol.ui.Search.Display = mol.ui.Display.extend(
        {
            init: function(config) {
                this._super('<div>Search.Display</div>');
                this.setStyleName('mol-Search-Display');
                this._config = config;
            }
        }
    );
};
