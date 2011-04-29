/**
 * Utilities.
 */
MOL.modules.util = function(mol) {
    mol.util = {};
    
    mol.util. urlEncode = function(obj) {
        var str = [];
        for(var p in obj)
            str.push(p + "=" + encodeURIComponent(obj[p]));
        return str.join("&");
    };
};