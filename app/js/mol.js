/**
 * Copyright 2010 Andrew W. Hill, Aaron Steele
 * 
 * 
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
















