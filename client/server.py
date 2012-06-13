import datetime, time
import json
import subprocess
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path 
from tornado.options import define, options, parse_command_line

define("port", default=8000, help="run on the given port", type=int)
define("arch", default="x86_64", help="platform architecture, valid value: i686 or x86_64", type=str)

cutybin = ""

def file_path(relative) :
    abspath = os.path.abspath(__file__)
    return os.path.join(os.path.dirname(abspath), relative)

def domain_path(relative) :
    return os.path.join('http://localhost:8000', relative)

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
        itemList = json.loads(self.get_argument('itemList'))
        print str(itemList)

        loader = tornado.template.Loader(file_path(""))
        
        itemHTML = ""
        for item in itemList:
            if item['type'] == 'text':
                itemHTML += loader.load('_text_item.html').generate(text = item['text'], height = item['height'])
            elif item['type'] == 'image':
                itemHTML += loader.load('_image_item.html').generate(image_url = item['image_url'], width = item['width'])

        html = loader.load("_render.html").generate( content = itemHTML )
        print html

        #format file name
        global fid
        if (fid>99999):
            fid=0
        else:
            fid=fid+1
        now=datetime.datetime.now()
        filename = now.strftime("%Y%m%dT%H%M%S") + "F" + str(fid)
        #filename = "out"
        domain_src_file = domain_path('static/render/' + filename + '.html')
        local_src_file = file_path('static/render/' + filename + '.html')
        output_file = file_path('static/render/' + filename + '.jpg')

        print "=========RENDER FILE======="
        f = open(local_src_file,'w')
        f.write(html)
        f.close()

        print local_src_file + ' written'

        print "=======HTML -> IMG========="
        print "output file: " + output_file
        cmd = "./../bin/{0} --min-width=0 --url={1} --out={2}".format(cutybin, domain_src_file, output_file)
        print "cmd: " + cmd
        subprocess.Popen(cmd, shell=True)
        print "==========END=============="
        
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
    cutybin = "CutyCapt-x64" if options.arch == "x86_64" else "CutyCapt-i686"

    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
