All the Javascripts for MoL.

 - mol.js: The main constructor for the entire environment.

All the modules "meet" in mol.js, allowing them all to
access each other. Each UI module has an 'engine' and a 
'display'.

Engines are derived from mol.ui.Map.Engine (see mol.ui.js).
All engines are created with two parameters:
    api:    (type: mol.ajax.Api)
            Used to communicate with the server.
    bus:    (type: mol.events.Bus)
            The bus is a single, shared event bus for the
            entire application.

    The api object uses has an 'execute(action, callback)'
    method, which 
    action:     JSON code
    callback:   callback.onsuccess(..) is called is fine

Displays drive the display, and are derived from
mol.ui.Display (see mol.ui.js).
    Calling the '_html()' method on any display returns the 
    HTML rendering for that display.

    All the UI specific code (such as Jquery) goes in the display

