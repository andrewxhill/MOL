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

MOL.src.files = [
    'mol.app.js', 
    'mol.events.js', 
    'mol.ajax.js', 
    'mol.log.js', 
    'mol.exceptions.js', 
    'mol.location.js', 
    'mol.model.js', 
    'mol.ui.js',
    'mol.ui.ColorSetter.js', 
    'mol.ui.LayerControl.js', 
    'mol.ui.LayerList.js', 
    'mol.ui.Map.js', 
    'mol.ui.Search.js'
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
















