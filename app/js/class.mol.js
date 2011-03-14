/*--------------------------------------------------------------------------.
|  Software: PhyloBox       		                                  		|
|   Version: 1.0                                                            |
|   Contact: andrewxhill@gmail.com || sander@digijoi.com                    |
| ------------------------------------------------------------------------- |
|     Admin: Andrew Hill (project admininistrator)                          |
|   Authors: Sander Pick, Andrew Hill                                    	|                     
| ------------------------------------------------------------------------- |
|   License: Distributed under the General Public License (GPL)             |
|            http://www.gnu.org/licenses/licenses.html#GPL                  |
| This program is distributed in the hope that it will be useful - WITHOUT  |
| ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or     |
| FITNESS FOR A PARTICULAR PURPOSE.                                         |
'--------------------------------------------------------------------------*/
/*###########################################################################
############################################################# CLASS FRAMEWORK  
###########################################################################*/
// Inspired by base2 and Prototype - John Resig
(function() {
	var initializing = false, fnTest = /xyz/.test(function(){xyz;}) ? /\b_super\b/ : /.*/;
	this.Class = function(){};
	Class.extend = function(prop) {
    	var _super = this.prototype;
    	initializing = true;
    	var prototype = new this();
    	initializing = false;
    	for(var name in prop) {
      		prototype[name] = typeof prop[name] == "function" &&
        	typeof _super[name] == "function" && fnTest.test(prop[name]) ?
        	(function(name,fn){
          		return function() {
            		var tmp = this._super;
            		this._super = _super[name];
            		var ret = fn.apply(this,arguments);       
            		this._super = tmp;
            		return ret;
          		};
        	})(name,prop[name]) :
        	prop[name];
    	}
		function Class() {
      		if(!initializing && this.init) this.init.apply(this,arguments);
    	}
    	Class.prototype = prototype;
    	Class.constructor = Class;
    	Class.extend = arguments.callee;
    	return Class;
	};
})();
//####################################################################### END