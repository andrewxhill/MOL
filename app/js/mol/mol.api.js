/**
 * Asynchronous callback that handles success and failure callbacks.
 */
mol.api.AsyncCallback = function(onSuccess, onFailure) {
    if (!(this instanceof mol.api.AsyncCallback)) {
        return new mol.api.AsyncCallback(onSuccess, onFailure);
    }
    this.onSuccess = onSuccess;
    this.onFailure = onFailure;
    return this;
};

/**
 * The API proxy used to execute requests.
 */
mol.api.ApiProxy = function() {
    if (!(this instanceof mol.api.ApiProxy)) {
        return new mol.api.ApiProxy();
    }
    this.execute = function(request, cb) {
        if (request.action === 'search') {
            var xhr = $.post('/api/taxonomy', request.params, 'json');
            xhr.success(cb.onSuccess);
            xhr.error(cb.onError);
        } else if (request.action === 'rangemap_metadata') {
            var xhr = $.post('/api/tile/metadata/'+ request.params.speciesKey);
            xhr.success(cb.onSuccess);
            xhr.error(cb.onError);
         } else if (request.action === 'points') {
            var xhr = $.post('/api/points/gbif/'+ request.params.speciesKey);
            xhr.success(cb.onSuccess);
            xhr.error(cb.onError);
        } 
    };
    return this;
};
