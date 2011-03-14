var mol = mol || {};    

/**
 * Helper for building namespaces.
 * 
 * @param namespace The namespace to build within mol global namespace
 */
mol.ns = function(namespace) {
    var parts = namespace.split('.'),
        parent = mol;
    var i;
    if (parts[0] === 'mol') {
        parts = parts.slice(1);
    }
    for (i = 0; i < parts.length; i += 1) {
        if (typeof parent[parts[i]] === 'undefined') {
            parent[parts[i]] = {};
        }
        parent = parent[parts[i]];
    }
    return parent;
};

mol.ns('mol.util');
mol.ns('mol.control');
mol.ns('mol.event');
mol.ns('mol.api');
mol.ns('mol.view');
mol.ns('mol.activity');

/**
 * Logging via Speed Tracer Logging API.
 * 
 * @param msg the message to log
 */
mol.util.log = function log(msg) {
    var logger = window.console;
    if (logger && logger.markTimeline) {
        logger.markTimeline(msg);
    }
};

/**
 * Helper that returns a boolean based on a string. Returns true if string is
 * 'true', returns false if string is 'false', otherwise returns false.
 * 
 * @param s The s to test 
 */
mol.util.isBool = function (s) {
    return (/^true$/i).test(s);
};

/**
 * Helper that serializes an object into a URL encoded GET query string.
 * 
 * @param obj The object to serialize
 */
mol.util.serializeQuery = function(obj) {
    var str = [];
    for(var p in obj)
        str.push(p + "=" + encodeURIComponent(obj[p]));
    return str.join("&");
};

/**
 * Helper that parses a URL encoded GET query string into an object.
 * 
 * @param query The query string
 */
mol.util.parseQuery = function(query) {
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
