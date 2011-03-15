/**
 * Constructor for PointsEngine.
 * 
 * @constructor
 * @param source The data source
 */
mol.engines.PointsEngine = function(source) {
    this.type = 'points';
    this.source = source;
    this.name = '';
    switch (source) {
    case "gbif":
        if (!this.name) {
            this.showUi();
        } else {
            // TODO
        }
        break;
    }
};

/**
 * Shows a UI for a PointsEngine.
 */
mol.engines.PointsEngine.prototype.showUi = function() {
    var dialog = $("div");
    $(dialog).append($('<div id="add_points_dialog" class="dialog_button output">Get GBIF Points<input type="search" id="gbif_points_search_box"><a href="javascript:" id="gbif_points_search">Go</a></div>'));    
};

// =============================================================================

/**
 * Constructor for a RangeEngine.
 * 
 * @constructor
 * @param source The data source
 */
mol.engines.RangeEngine = function(source) {
    this.type = 'range';
    this.source = source; 
    this.name = '';
    switch (source) {
    case "mol":
        if (!this.name){
            this.showUi();
        } else {
            // TODO
        }
        break;
    }
};

/**
 * Shows a UI for a RangeEngine.
 */
mol.engines.RangeEngine.prototype.showUi = function() {
    var dialog = $("div");
    $(dialog).append($('<div id="add_range_dialog" class="dialog_button output">Get MOL Range Map<input type="search" id="mol_range_search_box"><a href="javascript:" id="mol_range_search">Go</a></div></div>'));
};

