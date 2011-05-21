/**
 * Utilities.
 */
MOL.modules.util = function(mol) {
    mol.util = {};
    
    mol.util.urlEncode = function(obj) {
        var str = [];
        for(var p in obj)
            str.push(p + "=" + encodeURIComponent(obj[p]));
        return str.join("&");
    };

    /**
     * Parses a URL encoded GET query string into a JavaScript object.
     * 
     * @param query The query string
     */
    mol.util.urlDecode = function(query) {
        var e,
        a = /\+/g,  
        r = /([^&=]+)=?([^&]*)/g,
        d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
        q = query.replace('#', '').replace('?', '');
        var urlParams = {};
        while ((e = r.exec(q))) {
            urlParams[d(e[1])] = d(e[2]);
        }
        return urlParams;
    };

};