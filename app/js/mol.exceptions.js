/**
 * Exceptions module for handling exceptions.
 */
MOL.modules.exceptions = function(mol) {
    mol.exceptions = {};
    
    mol.exceptions.Error = Class.extend(
        {
            init: function(msg) {
                this._msg = msg;
            },

            getMessage: function() {
                return this._msg;
            }
        }
    );

    mol.exceptions.NotImplementedError = mol.exceptions.Error.extend(
    );

    mol.exceptions.IllegalArgumentException = mol.exceptions.Error.extend(
    );
};
