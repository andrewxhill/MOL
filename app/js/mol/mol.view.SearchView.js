/**
 * Search view that dispatches user events to an activity.
 * 
 * @constructor
 */
mol.view.SearchView = Backbone.View.extend(
{
    el: $('#SearchView'), 
    
    // TODO: This is not working... workaround via JQuery in initialize():
    events: {
        "keyup #searchBox": "searchBoxKeyUp",
        "click #searchButton": "searchButtonClick"
    },
    
    /**
     * Initializes the view.
     */
    initialize: function() {
        this.box = $('#searchBox');
        this.box.keyup(this.searchBoxKeyUp());
        this.button = $('#searchButton');
        this.button.click(this.searchButtonClick());
        this.checkbox = $('#cb');
        this.checkbox.change(this.searchButtonClick());
        $('#cbtext').click(this.checkBoxTextClick());
        this.tableContainer = $('#searchTable')[0];
        this.table = new google.visualization.Table(this.tableContainer);
    },
    
    checkBoxTextClick: function() {
        var self = this;
        return function(evt) {
            self.setMapsCheckbox(!self.isMapsChecked());
            self.searchButtonClick()();
        };
    },
    
    clearTable: function() {
        this.tableContainer.innerHTML = '';
    },
    
    isMapsChecked: function() {
        return this.checkbox.is(':checked');
    },
    
    setMapsCheckbox: function(isChecked) {
        this.checkbox.attr('checked', isChecked);
    },
    
    setActivity: function(activity) {
        this.activity = activity;
    },
        
    /**
     * Returns the text in the search box.
     */
    getSearchText: function() {
        return this.box.val() || this.box.attr('placeholder');
    },
    
    /**
     * Handles keyup event on the #searchBox and dispatches to activity.
     */
    searchBoxKeyUp: function(evt) {
        var self = this;
        return function(evt) {
            self.activity.searchBoxKeyUp(evt);                
        };
    },
    
    /**
     * Sets search button enabled property.
     */
    setSearchButtonEnabled: function(isEnabled) {
        var val = isEnabled ? '' : 'disabled';
        this.button.attr('disabled', val);        
    },

    /**
     * Handles click event on the #searchButton and dispatches to activity.
     */
    searchButtonClick: function(evt) {
        var self = this;
            return function(evt) {
                self.activity.searchButtonClick(evt);
            };
    },
    
    /**
     * Sets the #searchBox text.
     */
    setSearchText: function(t) {            
        this.box.val(t);
    }
});
