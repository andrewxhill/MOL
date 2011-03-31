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
                this._bindDisplay(new mol.ui.Search.Display({}));
                //this._bindDisplay(container);
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
                            restart: '',
                            close: '', 
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
                },
                widget = null;

                this._display = display;
                display.setEngine(this);

                display.hide();

                this._addLayerControlEventHandler();                
                
                // Restart button:
                widget = display.getRestartButton();
                //widget.text(config.text.restart);
                widget.click(
                    function(event) {
                        // TODO
                    }
                );
                
                // Close button:
                widget = display.getCloseButton();
                //widget.text(config.text.close);
                widget.click(
                    function(event) {
                        display.hide();
                    }
                );
  
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
                    display = this._display,
                    DisplayPosition = mol.ui.Map.Control.DisplayPosition,
                    ControlPosition = mol.ui.Map.Control.ControlPosition,
                    action = 'add',
                    config = {
                        display: display,
                        action: action,
                        displayPosition: DisplayPosition.TOP,
                        controlPosition: ControlPosition.CENTER_TOP
                    };
                bus.fireEvent(new MapControlEvent(config));     
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
                this._super();
                this.setInnerHtml(this._html());
                this._config = config;
            },
            getRestartButton: function(){
                return this.findChild('#searchRestart');
            },
            getCloseButton: function(){
                return this.findChild('#searchCancel');
            },
            getTypeSelectBox: function(){
                return this.findChild('.source');
            }, 
            getSearchBox: function(){
                return this.findChild('.value');
            }, 
            getGoButton: function() {
                return this.findChild('.execute');
            },
            getSearchWidget: function(){
                return this.findChild('.mol-LayerControl-Search');
            },
            getNextButton: function(){
                return this.findChild('.nextPage');
            },
            getAddButton: function(){
                return this.findChild('.addAll');
            },
            getNewResult: function(){
                var _result = this._super('<ul class="result">' +
                                '    <div class="resultName">' +
                                '        <div class="resultNomial"></div>' +
                                '        <br/>' +
                                '        <div class="resultAuthor"></div>' +
                                '    </div>' +
                                '    <div class="resultLink"><a href="/static/dead_link.html">more info</a></div>' +
                                '    <div class="buttonContainer"> ' +
                                '        <input type="checkbox" class="checkbox" /> ' +
                                '        <span class="customCheck"></span> ' +
                                '    </div> ' +
                                '</ul>');
                this.findChild('.mol-LayerControl-Results .searchResults').append(_result);
                return _result;
            },
            _html: function(){
                return '<div class="mainSearchNavigation">' +
                       '    <button id="searchCancel">' +
                       '         <img src="/static/cancel.png" />' +
                       '    </button>' +
                       '    <button id="searchRestart">' +
                       '         <img src="/static/reload.png" />' +
                       '    </button>' +
                       '</div>' +
                       '<div class="mol-LayerControl-Search widgetTheme">' +
                       '   <div class="title">Search:</div>' +
                       '   <select name="source" class="source">' +
                       '       <option value="range: MOL">MOL Range Maps</option>' +
                       '       <option value="points: GBIF">GBIF Occ Points</option>' +
                       '   </select>' +
                       '   <input class="value" type="text" />' +
                       '   <button class="execute">Go</button>' +
                       '</div>' +
                       '<div class="mol-LayerControl-Results">' +
                       '   <ol class="searchResults widgetTheme">' +
                       '   </ol>' +
                       '    <div class="navigation">' +
                       '        <button class="addAll">Add</button>' +
                       '        <button class="nextPage">Next Page</button>' +
                       '    </div>' +
                       '</div>';
            }
        }
    );
};
