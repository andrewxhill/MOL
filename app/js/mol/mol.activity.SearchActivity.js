/**
 * The search activity.
 * 
 * @constructor
 */
mol.activity.SearchActivity = function(view) {
    if (!(this instanceof mol.activity.SearchActivity)) {
        return new mol.activity.SearchActivity(view);
    }
    var self = this,
        addListener = google.visualization.events.addListener;
    this.view = view;
    this.view.setActivity(this);
    this.table = this.view.table;
    this.pageSize = 10;
    this.limit = 10;
    this.offset = 0;
    this.currentDataTable = null;
    this.currentPageIndex = 0;
    
    // Wires the up callback for table paging:
    addListener(this.view.table, 'page', 
                function(e) {
                    self.handlePage(e);
                });
                   
    // Configures query options:
    this.tableOptions = {
        page: 'event', 
        showRowNumber: true,
        allowHtml: true, 
        pagingButtonsConfiguration: 'both',
        pageSize: this.pageSize
    };
    
    this.updatePagingState(0);
    return this;
};

/**
 * Updates the paging state based on a page index.
 * 
 * @param pageIndex The page index
 */
mol.activity.SearchActivity.prototype.updatePagingState = function(pageIndex) {
    var pageSize = this.pageSize,
        dataTable = this.currentDataTable,
        newStartRow = -1;        
    if (pageIndex < 0) {
        return false;
    }
    if ((pageIndex == this.currentPageIndex + 1) && dataTable) {
        if (dataTable.getNumberOfRows() <= pageSize) {
            return false;
        }
    }
    this.currentPageIndex = pageIndex;
    newStartRow = this.currentPageIndex * pageSize;
    this.offset = newStartRow;
    // Note: row numbers are 1-based yet dataTable rows are 0-based.
    this.tableOptions['firstRowNumber'] = newStartRow + 1;
    return true;
};

/**
 * Sends an API request for data and draws the results via async callback.
 * 
 * @param saveLoc True to save a history location in the browser
 */
mol.activity.SearchActivity.prototype.sendAndDraw = function(saveLoc) {
    var cb = new mol.api.AsyncCallback(this.onSuccess(), this.onFailure()),
    params = this.getSearchParams(),
    historyState = this.getHistoryState();
    this.table.setSelection([]);
    mol.apiProxy.execute({action: 'search', params: params}, cb);
    if (saveLoc) {
        mol.controller.saveLocation(mol.util.serializeQuery(historyState));            
    }
};

/**
 * Handles a paging request from the table.
 * 
 * @param properties Contains the page (1, -1, or 0)
 */
mol.activity.SearchActivity.prototype.handlePage = function(properties) {
    this.view.setSearchButtonEnabled(false);
    var localTableNewPage = properties['page'], // 1, -1 or 0
        newPage = 0;
    if (localTableNewPage != 0) {
        newPage = this.currentPageIndex + localTableNewPage;
    }
    if (this.updatePagingState(newPage)) {
        this.sendAndDraw(true);
    }
};

/**
 * Goes to a place that is provided by the controller.
 * 
 * @param place The place object to go to
 */
mol.activity.SearchActivity.prototype.go = function(place) {
    var params = place.params,
        q = params.q,
        offset = Number(params.offset),
        limit = Number(params.limit),
        maps = mol.util.isBool(params.maps),
        newStartRow = -1,
        initialLoad = this.currentDataTable == null,
        pageIndex = -1,
        currentMapsValue = this.view.isMapsChecked();
    
    // Handles an initial load without params:
    if (!q && !maps) {
        this.view.setSearchText('');
        this.view.setMapsCheckbox(true);
        this.view.clearTable();
        return;
    }
    // Updates state:
    this.offset = ((offset != null) && offset >= 0) ? offset : this.offset;
    this.limit = ((limit != null) && limit >= 0) ? limit : this.limit;
    this.pageSize = this.limit;
    this.tableOptions['pageSize'] = this.pageSize;
    if (currentMapsValue != maps) {
        pageIndex = 0;
    } else {
        pageIndex = this.offset / this.pageSize;           
    }
    // Updates view:
    this.view.setSearchText(q);
    this.view.setMapsCheckbox(maps);   
    if (this.updatePagingState(pageIndex)) {
        this.sendAndDraw(true);        
    }
};

/**
 * Clicks the search button if the enter key was pressed.
 * 
 * @param evt The click event
 */
mol.activity.SearchActivity.prototype.searchBoxKeyUp = function(evt) {
    if (evt.keyCode === 13) {
        this.searchButtonClick(evt);
    }
};

/**
 * Gets the search params to be sent with an API request.
 */
mol.activity.SearchActivity.prototype.getSearchParams = function() {
    return {
        q: this.view.getSearchText(),
        limit: this.limit + 1,
        offset: this.offset,
        maps: this.view.isMapsChecked(),
        tqx: true
    };
};

/**
 * Gets the history token for saving the current location.
 */
mol.activity.SearchActivity.prototype.getHistoryState = function() {
    return {
        q: this.view.getSearchText(),
        limit: this.limit,
        offset: this.offset,
        maps: this.view.isMapsChecked(),
        tqx: true
    };
};

/**
 * Async callback for successful API requests.
 */
mol.activity.SearchActivity.prototype.onSuccess = function() {
    var self = this;
    return function(json) {
        self.view.setSearchButtonEnabled(true);
        var data = null;
        self.currentDataTable = null;
        google.visualization.errors.removeAll(self.view.tableContainer);        
        eval("data = " + json);
        self.currentDataTable = new google.visualization.DataTable(data);
        self.table.draw(self.currentDataTable, self.tableOptions);
        if (self.currentDataTable.getNumberOfRows() == 0) {
            google.visualization.errors.addError(
                self.view.tableContainer, 
                'No results',
                '', 
                {'showInTooltip': false});      
        }
    };
};

/**
 * Async callback for problematic API requests.
 */
mol.activity.SearchActivity.prototype.onFailure = function() {
    var self = this;
    return function(error) {
        alert('Failure: ' + error);
        self.view.setSearchButtonEnabled(true);
    };
};

/**
 * Handles a user search button click and also saves a browser location.
 * 
 * @param evt The button click event
 */
mol.activity.SearchActivity.prototype.searchButtonClick = function(evt) {
    this.view.setSearchButtonEnabled(false);
    this.offset = 0;
    this.currentPageIndex = 0;
    this.tableOptions['firstRowNumber'] = 1;
    this.sendAndDraw(true);
};
