import datetime, time
import json
import subprocess
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path 
from tornado.options import define, options, parse_command_line

define("port", default=8000, help="run on the given port", type=int)

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


global fid
fid=0

# Json
class Render(tornado.web.RequestHandler):
    def post(self,*args,**kwargs):
        content = self.get_argument('content')
        html = tornado.template.Loader(file_path("")).load("_render.html").generate( content = content )
        print html

        #format file name
        global fid
        if (fid>99999):
            fid=0
        else:
            fid=fid+1
        now=datetime.datetime.now()
        filename = now.strftime("%Y%m%dT%H%M%S") + "F" + str(fid)
        src_file = file_path('static/render/' + filename + '.html')
        output_file = file_path('static/render/' + filename + '.jpg')

        print "====================="
        print "assgning filename and saveing file"

        f = open(src_file,'w')
        f.write(html)
        f.close()

        print src_file + 'written'

        print "====================="
        print "running HTML->IMG"
        print "filename: " + filename
        subprocess.call(["./../bin/wkhtmltoimage-amd64", src_file, output_file])
        print "====================="
        print "returning..."
        
        resp = {    'success' : True,
                    'error' : None,
                    'image_url' : '/static/render/' + filename + '.jpg'
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
    parse_command_line()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
