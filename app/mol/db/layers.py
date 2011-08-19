from ndb import model

# New workflow models

class Layer(model.Model):
    source = model.StringProperty(required=True)     # e.g., jetz
    collection = model.StringProperty(required=True) # e.g., mammals
    filename = model.StringProperty(required=True)   # e.g., puma_concolor
    json = model.TextProperty()         # e.g., all metadata as JSON

class LayerPolygon(model.Model):
    # Required DBF fields
    areaid = model.StringProperty(required=True)
    bibliographiccitation = model.StringProperty(required=True)
    polygonid = model.StringProperty(required=True)
    polygonname = model.StringProperty(required=True)
    scientificname = model.StringProperty(required=True)
    # Optional DBF fields
    areaname = model.StringProperty()
    contributor = model.StringProperty()
    dateend = model.StringProperty()
    datestart = model.StringProperty()
    establishmentmeans = model.StringProperty()
    infraspecificepithet = model.StringProperty()
    occurrencestatus = model.StringProperty()
    seasonality = model.StringProperty()


class LayerIndex(model.Model):
    # The LayerPolygon
    polygon = model.StructuredProperty(LayerPolygon, repeated=True)
    # Full text corpus
    corpus = model.StringProperty('c', repeated=True)
    # Required fields
    json = model.TextProperty(required=True)
    accessrights = model.StringProperty(required=True)
    bibliographiccitation = model.StringProperty(required=True)
    breedingdomain = model.StringProperty(required=True)
    contact = model.StringProperty(required=True)
    coverage = model.StringProperty(required=True)
    date = model.StringProperty(required=True)
    email = model.StringProperty(required=True)
    eventdate = model.StringProperty(required=True)
    nonbreedingdomain = model.StringProperty(required=True)
    presencedefault = model.StringProperty(required=True)
    samplingprotocol = model.StringProperty(required=True)
    scientificname = model.StringProperty(required=True)
    source = model.StringProperty(required=True)
    verbatimsrs = model.StringProperty(required=True)
    # Optional fields
    accessright = model.StringProperty()
    contributor = model.StringProperty()
    format = model.StringProperty()
    identifier = model.StringProperty()
    rights = model.StringProperty()
    samplingprotocol = model.StringProperty()
    surveyintervals = model.StringProperty()
    type = model.StringProperty()

