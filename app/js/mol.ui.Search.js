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
                            restart: 'refart',
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
                },
                widget = null;

                this._display = display;
                display.setEngine(this);

                display.hide();

                this._addLayerControlEventHandler();                
                
                // Restart button:
                widget = display.getRestartButton();
                widget.text(config.text.restart);
                widget.click(
                    function(event) {
                        // TODO
                    }
                );
                
                // Close button:
                widget = display.getCloseButton();
                widget.text(config.text.close);
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
  
                widget = display.getTypeSelectBox();
                widget.hide();
                widget.change(
                    function(event) {
                        var selection = display.getTypeSelectBox().val();
                        mol.log.info('Search.Display.TypeSelectBox.change() - ' + selection);
                    }
                );

                // display.getTypeSelectBox().click(
                //     function(event) {
                //         mol.log.info('Search.Display.CloseButton.click()');
                //     }
                // );
                
                widget = display.getSearchBox();
                widget.hide();
                widget.click(
                    function(event) {
                        mol.log.info('Search.Display.SearchBox.click()');                        
                    }
                );
  
                widget = display.getGoButton();
                widget.hide();
                widget.click(
                    function(event) {
                        var query = display.getSearchBox().getText();
                        mol.log.info('Search.Display.GoButton.click() with search: ' + query);                       
                    }
                );

                display.getSearchWidget().hide();
                display.getLoadingWidget().hide();
                display.getNextButton().hide();
                display.getAddButton().hide();

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
                return this.findChild('#restart');
            },
            getCloseButton: function(){
                return this.findChild('#cancelAll');
            },
            getSelectButton: function(){
                return this.findChild('.mol-LayerControl-DataType');
            }, 
            getTypeSelectBox: function(){
                return this.findChild('.searchSource');
            }, 
            getSearchBox: function(){
                return this.findChild('.searchValue');
            }, 
            getGoButton: function() {
                return this.findChild('.searchExecute');
            },
            getSearchWidget: function(){
                return this.findChild('.mol-LayerControl-Search');
            },
            getLoadingWidget: function(){
                return this.findChild('.mol-LayerControl-Loading');
            },
            getNextButton: function(){
                return this.findChild('.addAll');
            },
            getAddButton: function(){
                return this.findChild('.nextPage');
            },
            getNewResult: function(){
                var _result = this._super('<ul class="result widgetTheme">' +
                          '    <div class="resultName">name' +
                          '        <div class="resultNomial">(name)</div>' +
                          '        <br/>' +
                          '        <div class="resultAuthor">(author)</div>' +
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
                return  '<button id="restart">restart</button>' +
                        '<button id="cancelAll">close</button>' +
                        '<div class="mol-LayerControl-DataType widgetTheme">' +
                        '      <div class="selectLabel">Select</div>' +
                        '      <button class="rangeTypeSelect">Range Map</button>' +
                        '      <button class="pointsTypeSelect">Occ. Points</button>' +
                        '</div>' +
                        '<div class="mol-LayerControl-Search widgetTheme">' +
                        '  <select name="searchSource" class="searchSource">' +
                        '      <option value="MOL">MOL</option>' +
                        '  </select>' +
                        '  <input class="searchValue" type="text" />' +
                        '  <button class="searchExecute">Go</button>' +
                        '</div>' +
                        '<div class="mol-LayerControl-Loading widgetTheme">' +
                        '    <div><img src="/static/loading-small.gif" /></div> <div>Searching...</div>' +
                        '</div>' +
                        '<div class="mol-LayerControl-Results">' +
                        '  <ol class="searchResults">' +
                        '  </ol>' +
                        '  <div class="navigation">' +
                        '      <button class="addAll">Add</button>' +
                        '      <button class="nextPage">Next Page</button>' +
                        '  </div>' +
                        '</div>';
            }
        }
    );
};
