from google.appengine.ext import db

#This is the datastore model that is needed in your App to use the bulk loader
#We will be working to optimize and error check all of this as we go.


class hard_coded_taxon_lists(db.Model):
    rank = db.StringProperty()
    accepted_names_only = db.BooleanProperty()
    name = db.StringProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class hard_coded_species_totals(db.Model):
    taxon = db.StringProperty()
    species_count = db.IntegerProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class references(db.Model):
    record_id = db.IntegerProperty()
    author = db.StringProperty()
    year = db.IntegerProperty()
    title = db.StringProperty()
    source = db.StringProperty()
    database_id = db.IntegerProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
    
class scientific_name_references(db.Model):
    record_id = db.IntegerProperty()
    name_code = db.StringProperty()
    reference_type = db.StringProperty()
    reference_id = db.IntegerProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class specialists(db.Model):
    record_id = db.IntegerProperty()
    specialist_name = db.StringProperty()
    database_id = db.IntegerProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class taxa(db.Model):
    record_id = db.IntegerProperty()
    lsid = db.StringProperty()
    name = db.StringProperty()
    name_with_italics = db.StringProperty()
    taxon = db.StringProperty()
    name_code = db.StringProperty()
    parent_id = db.IntegerProperty()
    sp2000_status_id = db.IntegerProperty()
    database_id = db.IntegerProperty()
    is_accepted_name = db.BooleanProperty()
    is_species_or_nonsynonymic_higher_taxon = db.BooleanProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)

    
class sp200_statuses(db.Model):
    record_id = db.IntegerProperty()
    sp200_status = db.StringProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class simple_search(db.Model):
    record_id = db.IntegerProperty()
    taxa_id = db.IntegerProperty()
    words = db.StringProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class scientific_names(db.Model):
    record_id = db.IntegerProperty()
    name_code = db.StringProperty()
    web_site = db.LinkProperty()
    reference_id = db.IntegerProperty()
    genus = db.StringProperty()
    species = db.StringProperty()
    infraspecies = db.StringProperty()
    infraspecies_marker = db.StringProperty()
    author = db.StringProperty()
    accepted_name_code = db.StringProperty()
    comment = db.StringProperty()
    scrutiny_date = db.StringProperty()
    sp2000_status_id = db.IntegerProperty()
    database_id = db.IntegerProperty()
    specialist_id = db.IntegerProperty()
    family_id = db.IntegerProperty()
    is_accepted_name = db.BooleanProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
    
    
class common_names(db.Model):
    record_id = db.IntegerProperty()
    name_code = db.StringProperty()
    common_name = db.StringProperty()
    language = db.StringProperty()
    country = db.StringProperty()
    reference_id = db.IntegerProperty()
    database_id = db.IntegerProperty()
    is_infraspecies = db.BooleanProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
class families(db.Model):
    record_id = db.IntegerProperty()
    hierarchy_code = db.StringProperty()
    kingdom = db.StringProperty()
    phylum = db.StringProperty()
    class_ = db.StringProperty()
    order = db.StringProperty()
    family = db.StringProperty()
    superfamily = db.StringProperty()
    family_common_name = db.StringProperty()
    database_name = db.StringProperty()
    is_accepted_name = db.BooleanProperty()
    database_id = db.IntegerProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
    
class distribution(db.Model):
    record_id = db.IntegerProperty()
    name_code = db.StringProperty()
    distribution = db.TextProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
    
    
class databases(db.Model):
    record_id = db.IntegerProperty()
    database_name_displayed = db.StringProperty()
    database_name = db.StringProperty()
    database_full_name = db.StringProperty()
    web_site = db.LinkProperty()
    organization = db.StringProperty()
    contact_person = db.StringProperty()
    taxa = db.StringProperty()
    taxonomic_coverage = db.TextProperty()
    abstract = db.TextProperty()
    version = db.StringProperty()
    release_date = db.StringProperty()
    SpeciesCount = db.IntegerProperty()
    SpeciesEst = db.IntegerProperty()
    authors_editors = db.StringProperty()
    accepted_species_names = db.IntegerProperty()
    accepted_infraspecies_names = db.IntegerProperty()
    species_synonyms = db.IntegerProperty()
    infraspecies_synonyms = db.IntegerProperty()
    common_names = db.IntegerProperty()
    total_names = db.IntegerProperty()
    is_new = db.BooleanProperty()
    last_update = db.DateTimeProperty(auto_now_add=True)
