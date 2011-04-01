/**
 * This is the global MOL constructor for creating a sandbox environment composed
 * of modules. Everything that happens within this constructor is protected from
 * leaking into the global scope.
 * 
 */
function MOL() {
    var args = Array.prototype.slice.call(arguments),
        callback = args.pop(),
        modules = (args[0] && typeof args[0] === "string") ? args : args[0],
        i;
    if (!(this instanceof MOL)) {
        return new MOL(modules, callback);
    }
   
    if (!modules || modules === '*') {
        modules = [];
        for (i in MOL.modules) {
            if (MOL.modules.hasOwnProperty(i)) {
                modules.push(i);
            }
        }
    }
    for (i = 0; i < modules.length; i += 1) {
        MOL.modules[modules[i]](this);
    }
    callback(this);
    return this;
};

MOL.modules = {};

MOL.src = {};

MOL.src.makeId = function() {
    var text = "",
        possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for( var i=0; i < 5; i++ ) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
};

MOL.src.files = [
    'mol.app.js?id=' + MOL.src.makeId(), 
    'mol.events.js?id=' + MOL.src.makeId(), 
    'mol.ajax.js?id=' + MOL.src.makeId(), 
    'mol.log.js?id=' + MOL.src.makeId(), 
    'mol.exceptions.js?id=' + MOL.src.makeId(), 
    'mol.location.js?id=' + MOL.src.makeId(), 
    'mol.model.js?id=' + MOL.src.makeId(), 
    'mol.ui.js?id=' + MOL.src.makeId(),
    'mol.ui.ColorSetter.js?id=' + MOL.src.makeId(), 
    'mol.ui.LayerControl.js?id=' + MOL.src.makeId(), 
    'mol.ui.LayerList.js?id=' + MOL.src.makeId(), 
    'mol.ui.Map.js?id=' + MOL.src.makeId(), 
    'mol.ui.Search.js?id=' + MOL.src.makeId()
];

/**
 * Dynamically loads JavaScript source modules by creating script elements and 
 * appending them to DOM in the head element.
 */
MOL.src.load = function() {
    var src = MOL.src.files,
        file = null,
        script = null;
    for (x in src) {
        file = "../../../js/" + src[x];
        script = document.createElement('script');
        script.setAttribute("type","text/javascript");
        script.setAttribute("src", file);
        document.getElementsByTagName("head")[0].appendChild(script);
    }
};
















