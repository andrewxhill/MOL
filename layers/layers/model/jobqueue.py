import meta
from layers import model

import types
Base = declarative_base()

from genericmodel import GenericDBRecord

class CoLNode(GenericDBRecord,Base):
    """Implements a record class to contain NCBI taxonomy nodes.  Each node also includes an TaxaName object
    that corresponds with the scientific name for the node."""
    __tablename__ = 'taxa'
    taxa_id = sa.Column("record_id",sa.types.Integer, primary_key=True)
    parent_id = sa.Column("parent_id",sa.types.Integer)
    rank = sa.Column("taxon",sa.types.String)
    scientificname = sa.Column("name",sa.types.String)
    
    def getchildren(self):
        """Retrieves all children of this node.
        
        :returns: A list of node TaxaNode objects containing all direct children of this node"""
        return meta.Session.query(CoLNode).filter(CoLNode.parent_id == self.taxa_id).all()

    def haschildren(self):
        """Check if this node has any child nodes.
        
        :returns: true if this node has one or more child nodes"""
        return meta.Session.query(CoLNode).filter(CoLNode.parent_id == self.taxa_id).count() > 0

    def hasdistribution(self):
        """Check if this node has a stored distribution.
        
        :returns: true if this node has one or more distributions"""
        return meta.Session.query(TaxonDistribution).filter(TaxonDistribution.taxa_id == self.taxa_id).count() > 0

class CoLName(Base,GenericDBRecord):
    """Implements a record class to contain NCBI names."""
    __tablename__ = 'aves_simple_search'
    record_id = sa.Column("record_id",sa.types.Integer, primary_key=True)
    """internal unique id"""
    taxa_id = sa.Column("taxa_id",sa.types.Integer, sa.schema.ForeignKey('taxa.taxa_id'))
    """the id of the taxonomy node for this name"""
    name_txt = sa.Column("words",sa.types.String)
    rank = sa.Column("rank",sa.types.String)
    
    def hasdistribution(self):
        """Check if this node has a stored distribution.
        
        :returns: true if this node has one or more distributions"""
        return meta.Session.query(TaxonDistribution).filter(TaxonDistribution.taxa_id == self.taxa_id).count() > 0


class TaxonDistribution(Base,GenericDBRecord):
    """Implements a record class to contain NCBI names."""
    __tablename__ = 'aves_distributions'
    """internal unique id"""
    record_id = sa.Column("record_id",sa.types.Integer, primary_key=True)
    """the id of the taxonomy node for this name"""
    taxa_id = sa.Column("taxa_id",sa.types.Integer, sa.schema.ForeignKey('taxa.taxa_id'))
    
    json_polygon = sa.Column("json_polygons",sa.types.String)
    

def jsonprep(record):
    """JSON conversion helper function that probably shouldn't be here.  Probably belongs in a higher-level
    module.  Included here to illustrate generic programming with record classes."""
    if isinstance(record, GenericDBRecord):
        return record.asdict(True)

    raise TypeError(repr(record) + " is not JSON serializable")

