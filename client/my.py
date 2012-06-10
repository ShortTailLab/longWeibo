import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path 
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

def file_path(relative) :
    return os.path.join(os.path.dirname(__file__), relative)

# Page
class Home(tornado.web.RequestHandler):
    def get(self):
        self.render(file_path("index.html"))

# Json
class UploadImage(tornado.web.RequestHandler):
    def post(self):
        f = self.request.files[u'files[]'][0]

        # now you can do what you want with the data, we will just save the file to an uploads folder
        upload_path = file_path("static/uploads/")
        output_file = open(upload_path + f['filename'], 'w')
        output_file.write(f['body'])

        name = f['filename']
        size = len(f['body'])

        resp = { 
            'name' : name,
            'size' : size,
            'url'  : '/static/uploads/' + name,
            'thunmnail_url' : '/static/uploads/' + name,
            'delete_url' : '',
            'delete_type' : 'DELETE',
        }

        self.finish(resp)

# Json
class Render(tornado.web.RequestHandler):
    def post(self):
        content = self.get_argument('content')
        html = tornado.template.Loader(file_path("")).load("_render.html").generate( content = content )
        print html
        resp = {    'success' : True,
                    'error' : None,
                    'image_url' : '/static/render/'
                }
        self.finish( resp )

settings ={
    "static_path" : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
}


application = tornado.web.Application([
    (r"/", Home),
    (r"/upload", UploadImage),
    (r"/render", Render),
], **settings);

if __name__ == "__main__":
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
