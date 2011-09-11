webapp_django_version = '1.2'

def webapp_add_wsgi_middleware(app):
    # Monkey patch that disables AppStats logging
    from google.appengine.ext.appstats import recording
    def save(self):
        try:        
            self._save()      
        except Exception:
            pass
    recording.Recorder.save = save
    app = recording.appstats_wsgi_middleware(app)
    return app

    # from google.appengine.ext.appstats import recording
    # app = recording.appstats_wsgi_middleware(app)
    # return app
