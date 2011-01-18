"""These classes define the generic DB data model.  These base classes should not be instantiated directly; rather, they should be extended by subclasses that access content in a specific database.

To derive a usable subclass, the child class needs to indicate the name of the database table it corresponds to via the __tablename__ class attribute and then add attributes representing the columns of the table to map.  Child classes will also need to inherit from the SQLAlchemy declarative base class.  The following code gives an example of how to derive a child class. ::
"""

import meta

class GenericDBRecord():
    """The generic base class that implements all basic functionality for subclasses that wrap DB records."""
    __tablename__ = ''

    def get(self, searchstring, **modifiers):
        """Factory method that returns a list of GenericDBRecord instances based on arbitrary search criteria.
        
        :arg searchstring: specifies search criteria, using standard SQL operators
        :type searchstring: string
        
        :keyword orderby: an attribute (table column) [asc|desc] by which to sort the results
        :type orderby: string
        :keyword limit: indicates how many result objects to return
        :type limit: integer
        :keyword offset: which result (numbered from 0) to start with
        :type offset: integer

        :returns: a list of record objects matching the search criteria
        
        Examples::
        
            # RecordClass is a subclass of GenericDBRecord
            RecordClass().get("id > 200")
            RecordClass().get("id > 200", orderby='name_txt', limit=10, offset=100)"""
        return self._buildquery(searchstring, modifiers).all()

    def getall(self, **modifiers):
        """Factory method that retrieves all instances of GenericDBRecord from the DB table.
        
        :keyword orderby: an attribute (table column) [asc|desc] by which to sort the results
        :type orderby: string
        :keyword limit: indicates how many result objects to return
        :type limit: integer
        :keyword offset: which result (numbered from 0) to start with
        :type offset: integer
        
        :returns: a list of all record objects in the database"""
        return self._buildquery('', modifiers).all()

    def asdict(self, recurse=False):
        """Convert the public attributes (e.g., table columns) of this object to a dictionary.
        
        :param recurse: optional; indicates if GenericDBRecord objects contained as member data in this object should be recursively processed
        :type recurse: boolean"""
        dict = {}
        for attrib in self.__dict__.keys():
            if not(attrib.startswith('_')):
                dict[attrib] = self.__dict__[attrib]
                if recurse and isinstance(self.__dict__[attrib], GenericDBRecord):
                    dict[attrib] = self.__dict__[attrib].asdict(True)

        return dict
