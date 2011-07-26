/**
 * UI module.
 */
MOL.modules.ui = function(mol) {
    
    mol.ui = {};
    
    /**
     * Interface for UI Engine classes.
     */
    mol.ui.Engine = Class.extend(
        {
            /**
             * Starts the engine and provides a container for its display.
             * 
             * @param container the container for the engine display 
             */
            start: function(container) {
                throw mol.exceptions.NotImplementedError;
            },
            
            /**
             * Gives the engine a new place to go based on a browser history
             * change.
             * 
             * @param place the place to go
             */
            go: function(place) {
                throw mol.exceptions.NotImplementedError;
            },
            
            /**
             * Gets an object of place state used to construct URL parameters.
             */
            getPlaceState: function() {
                throw mol.exceptions.NotImplementedError;
            }
        }
    );

    /**
     * Base class for DOM elements.
     */
    mol.ui.Element = Class.extend(
        {
            /**
             * Constructs a new Element from an element.
             */
            init: function(element) {
                if (!element) {
                    element = '<div>';
                }
                this._element = $(element);
            },
            
            /**
             * Returns the underlying DOM element object.
             */
            getElement: function() {
                return this._element;
            },
            
            /**
             * Proxies to JQuery.
             */
            change: function(handler) {
                this._element.change(handler);
            },
            
            attr: function(name, val) {
                if (val === undefined) {
                    return this._element.attr(name);
                } else {
                    return this._element.attr(name, val);                    
                }
            },

            /**
             * Proxies to JQuery to find parent element.
             */
            getParent: function(){
                return new mol.ui.Element(this._element.parent());
            },
            
            /**
             * Proxies to JQuery to find child element.
             */
            findChild: function(identfier){
                return new mol.ui.Element(this._element.find(identfier));
            },

            findChildren: function(id) {
                var res = new Array();
                this._element.children(id).each(function(c,v){
                    res.push(new mol.ui.Element(v));
                });
                return res;
            },
            

            find: function(id) {
                var res = new Array();
                this._element.find(id).each(function(c,v){
                    res.push(new mol.ui.Element(v));
                });
                return res;
            },
            
            text: function(text) {
                if (text) {
                    this._element.text(text);
                    return true;
                } else {
                    return this._element.text();
                }
            },

            select: function() {
                this._element.select();
            },
            
            src: function(src) {
                if (src) {
                    this._element.src = src;
                    return true;
                } else {
                    return this._element.src;
                }
            },

            /**
             * Proxies to JQuery.
             */
            val: function(val) {
                if (val) {
                    this._element.val(val);
                    return true;
                } else {
                    return this._element.val();    
                }                
            },
            
            /**
             * Proxies to JQuery.
             */
            setInnerHtml: function(html) {
                this._element.html(html);
            },

            /**
             * Proxies to JQuery.
             */
            getInnerHtml: function() {
                var html = this._element.html();
                return html;
            },

            /**
             * Proxies to JQuery.
             */
            isVisible: function() {
                if (!this._element.is(':visible')) {
                    return false;
                }
                return true;
            },

            setChecked: function(checked) {
                this.attr('checked', checked);
            },

            addClass: function(classname) {
                this._element.addClass(classname);
            },

            removeClass: function(classname) {
                this._element.removeClass(classname);                
            },

            isChecked: function() {
                if (!this._element.is(':checked')) {
                    return false;
                }
                return true;
            },
            
            /**
             * Proxies to JQuery UI.
             */
            disableSelection: function() {
                this._element.selectable({ disabled: true });
                return true;
            },

            /**
             * Proxies to JQuery.show()
             */
            show: function() {
                this._element.show();
            },
            
            /**
             * Proxies to JQuery.hide()
             */
            hide: function() {
                this._element.hide();                
            },

            /**
             * Proxy to JQuery.remove()
             */
            remove: function() {
                this._element.remove();
            },

            /**
             * Proxy to JQuery.click()
             */
            click: function(handler) {
                this._element.click(handler);
            },

            keyup: function(handler) {
                this._element.keyup(handler);
            },
            /**
             * Proxy to JQuery.append()
             */
            append: function(widget) {
                this._element.append(widget.getElement());
            },

            /**
             * Proxy to JQuery.prepend().
             */
            prepend: function(widget) {
                this._element.prepend(widget.getElement());
            },

            /**
             * Gets primary style name.
             */
            getStylePrimaryName: function() {
                var fullClassName = this.getStyleName(),
                    spaceIdx = fullClassName.indexOf(' ');
                if (spaceIdx >= 0) {
                    return fullClassName.substring(0, spaceIdx);
                }
                return fullClassName;
            },
            
            /**
             * Adds a secondary or dependent style name to this object.
             */
            addStyleName: function(style) {
                this._setStyleName(style, true);
            },
          
            /**
             * Adds a dependent style name by specifying the style name's suffix.
             */
            addStyleDependentName: function(styleSuffix) {
                this.addStyleName(this.getStylePrimaryName() + '-' + styleSuffix);
            },         

            focus: function() {
                this._element.focus();
            },
            
            fadeout: function(n) {
                var self = this;
                this._element.animate({opacity:0},3000,'swing', function(){self._element.remove()});
            },
            
            /**
             * Gets all of the object's style names, as a space-separated list.
             */
            getStyleName: function() {
                var classAttr = this.getElement().attr('class');
                if (!classAttr) {
                    return '';                    
                }
                return classAttr.split(/\s+/).join(' ');
            },
          
            /**
             * Clears all of the object's style names and sets it to the given 
             * style.
             */
            setStyleName: function(style) {
                var s = style.split(/\s+/).join(' ');
                this.getElement().attr('class', s);
            },

            /**
             * Removes a dependent style name by specifying the style name's 
             * suffix.
             */
            removeStyleDependentName: function(style) {
                 this.removeStyleName(this.getPrimaryStyleName() + '-' + style);
            },          

            /**
             * Removes a style.
             */
            removeStyleName: function(style) {
                this._setStyleName(style, false);
            },

            /**
             * Sets the object's primary style name and updates all dependent 
             * style names.
             */
            setStylePrimaryName: function(style) {
                style = $.trim(style);
                if (style.length == 0) {
                    throw mol.exceptions.IllegalArgumentException;
                }
                this._updatePrimaryAndDependentStyleNames(style);
            },

            _setStyleName: function(style, add) {
                var oldStyle, idx, last, lastPos, begin, end, newClassName;
                style = $.trim(style);
                if (style.length == 0) {
                    throw mol.exceptions.IllegalArgumentException;
                }

                // Get the current style string.
                oldStyle = this.getStyleName();
                idx = oldStyle.indexOf(style);

                // Calculate matching index.
                while (idx != -1) {
                    if (idx == 0 || oldStyle.charAt(idx - 1) == ' ') {
                        last = idx + style.length;
                        lastPos = oldStyle.length;
                        if ((last == lastPos)
                            || ((last < lastPos) && (oldStyle.charAt(last) == ' '))) {
                            break;
                        }
                    }
                    idx = oldStyle.indexOf(style, idx + 1);
                }

                if (add) {
                    // Only add the style if it's not already present.
                    if (idx == -1) {
                        if (oldStyle.length > 0) {
                            oldStyle += " ";
                        }
                        this.setStyleName(oldStyle + style);
                    }
                } else {
                    // Don't try to remove the style if it's not there.
                    if (idx != -1) {
                        // Get the leading and trailing parts, without the removed name.
                        begin = $.trim(oldStyle.substring(0, idx));
                        end = $.trim(oldStyle.substring(idx + style.length));

                        // Some contortions to make sure we don't leave extra spaces.
                        if (begin.length == 0) {
                            newClassName = end;
                        } else if (end.length == 0) {
                            newClassName = begin;
                        } else {
                            newClassName = begin + " " + end;
                        }
                        this.setStyleName(newClassName);
                    }
                }
            },

             /**
              * Replaces all instances of the primary style name.
              */
            _updatePrimaryAndDependentStyleNames: function(newPrimaryStyle) {
                var classes = this.getStyleName().split(/\s+/);
                if (!classes) {
                    return;
                }                
                var oldPrimaryStyle = classes[0];
                var oldPrimaryStyleLen = oldPrimaryStyle.length;
                var name;                
                classes[0] = newPrimaryStyle;
                for (var i = 1, n = classes.length; i < n; i++) {
                    name = classes[i];
                    if (name.length > oldPrimaryStyleLen
                        && name.charAt(oldPrimaryStyleLen) == '-'
                        && name.indexOf(oldPrimaryStyle) == 0) {
                        classes[i] = newPrimaryStyle + name.substring(oldPrimaryStyleLen);
                    }
                }
                this.setStyleName(classes.join(" "));
            }
        }
    );

    /**
     * Base class for Displays.
     */
    mol.ui.Display = mol.ui.Element.extend(
        {
            /**
             * Constructs a new Display with the given DOM element.
             */
            init: function(element) {
                this._super(element);
            },
            
            /**
             * Sets the engine for this display.
             * 
             * @param engine a mol.ui.Engine subclass
             */
            setEngine: function(engine) {
                this._engine = engine;
            }
        }
    );
};
