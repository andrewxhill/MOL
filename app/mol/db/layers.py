from ndb import model

# New workflow models

class Layer(model.Model):
    """Models a single layer from a source collection."""

    source = model.StringProperty(required=True)     # e.g., jetz
    collection = model.StringProperty(required=True) # e.g., mammals
    filename = model.StringProperty(required=True)   # e.g., puma_concolor
    json = model.TextProperty(required=True)         # e.g., all metadata as JSON

class LayerPolygon(model.Model): 
    """Models a Layer polygon (for use as a StructuredProperty of LayerIndex)."""

    # Required MoL DBF fields (http://goo.gl/UkzJW)
    #
    polygonid = model.StringProperty(required=True)
    areaid = model.StringProperty(required=True)
    specieslatin = model.StringProperty(required=True)
    source = model.StringProperty(required=True)

    # Optional MoL DBF fields (http://goo.gl/UkzJW) dynamically added during 
    # bulkloading.
    #
    # abundance
    # abundancecomment
    # abundancemakeup
    # abundancemethod
    # abundancesurveyarea
    # abundanceunits
    # dateend
    # datestart
    # distributioncomment
    # measurementcomment
    # measurementmethod
    # seasonality
    # bibliographiccitation
    # contributor
    # dynamicproperties
    # establishmentmeans
    # infraspecificepithet
    # occurrencestatus
    # population
    # scientificname
    # taxonid
    # taxonremarks
        
class LayerIndex(model.Expando): # parent=Layer
    """Models a searchable model for Layer."""

    # All LayerPolygon entities for the Layer
    polygons = model.StructuredProperty(LayerPolygon, repeated=True)

    # Full text corpus
    corpus = model.StringProperty('c', repeated=True)
    
    # Required MOL metadata (http://goo.gl/98r46)
    #
    accessrights = model.StringProperty(required=True)
    bibliographiccitation = model.StringProperty(required=True)
    breedingdomain = model.StringProperty(required=True)
    contact = model.StringProperty(required=True)
    coverage = model.StringProperty(required=True)
    creator = model.StringProperty(required=True)
    date = model.StringProperty(required=True)
    description = model.StringProperty(required=True)
    email = model.StringProperty(required=True)
    eventdate = model.StringProperty(required=True)
    layertype = model.StringProperty(required=True)
    nonbreedingdomain = model.StringProperty(required=True)
    presencedefault = model.StringProperty(required=True)
    publisher = model.StringProperty(required=True)
    samplingprotocol = model.StringProperty(required=True)
    scientificname = model.StringProperty(required=True)
    source = model.StringProperty(required=True)
    subject = model.StringProperty(required=True)
    taxonomiccoverage = model.StringProperty(required=True)
    title = model.StringProperty(required=True)
    verbatimsrs = model.StringProperty(required=True)
    
    # Optional MoL metadata (http://goo.gl/98r46) dynamically added during 
    # bulkloading.
    #
    # accessright
    # basemaps: 
    # contributor
    # enddateaccuracy
    # format
    # identifier
    # language:
    # mapcount
    # maxregionsperspecies
    # maxx
    # maxy
    # medianregionsperspecies
    # minregionsperspecies
    # minx
    # miny
    # relation
    # rights
    # samplingprotocol
    # startdateaccuracy
    # taxonomy
    # type
