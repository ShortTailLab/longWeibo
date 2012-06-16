import datetime, time
import json
import subprocess
import random
import cStringIO
import shlex
from multiprocessing import Pool, Queue
from PIL import Image
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, tornado.gen
import os.path 
from tornado.options import define, options, parse_command_line

define("port", default=8000, help="run on the given port", type=int)
define("i386", default=False, help="use this option if running on 32bit system", type=bool)
define("xvfb", default=False, help="use this option if running on headless server", type=bool)
define("maxupload", default=2048, help="max uploaded image size, kb", type=bool)
RAND_FILE_NAME_LENGTH = 12

def file_path(relative) :
    abspath = os.path.abspath(__file__)
    return os.path.join(os.path.dirname(abspath), relative)

def domain_path(relative) :
    return os.path.join('http://localhost:' + str(options.port), relative)

def rand_string(length = RAND_FILE_NAME_LENGTH):
    s = ""
    for i in range(0, length):
        cap = random.randint(0,1) == 1
        r = random.randint(0, 25)
        if cap:
            s += chr(97 + r)
        else:
            s += chr(65 + r)
    return s

def save_thumbnail(s, out_path):
    image = cStringIO.StringIO(s)
    im = Image.open(image)
    # use real height, but contrain width to max displayable
    size = 480, im.size[1]
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(out_path, 'JPEG')

# Page
class Home(tornado.web.RequestHandler):
    def get(self):
        self.render(file_path("index.html"))

# Json
class UploadImage(tornado.web.RequestHandler):
    def post(self):
        f = self.request.files[u'files[]'][0]

        if len(f['body']) > (options.maxupload * 1024):
            self.send_error()
            return 

        iname, iext = os.path.splitext(f['filename'])
        if iext == "" or iext.lower() not in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif']:
            self.send_error({ 'name' : filename, 'size' : size, 'success' : False })
            return

        #name = f['filename']
        filename = rand_string() + iext
        print filename

        #
        upload_path = file_path("static/uploads/") + filename
        save_thumbnail(f['body'], upload_path)

        #output_file = open(upload_path + filename, 'w')
        #output_file.write(f['body'])

        size = len(f['body'])

        resp = { 
            'success' : True,
            'name' : filename,
            'size' : size,
            'url'  : '/static/uploads/' + filename,
            'thunmnail_url' : '/static/uploads/' + filename,
            'delete_url' : '',
            'delete_type' : 'DELETE',
        }

        self.finish(resp)


# Json
class Render(tornado.web.RequestHandler):
    
    @tornado.web.asynchronous
    @tornado.gen.engine
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

        filename = rand_string()
        domain_src_file = domain_path('static/render/' + filename + '.html')
        local_src_file = file_path('static/render/' + filename + '.html')
        output_file = file_path('static/render/' + filename + '.jpg')

        print "=========RENDER FILE======="
        f = open(local_src_file,'w')
        f.write(html)
        f.close()
	
    	cutybin = "CutyCapt-i686" if options.i386 else "CutyCapt-x64"
    	xvfb = 'xvfb-run --auto-servernum --server-args="-screen 0, 1024x768x24"' if options.xvfb else ""
        cmd = "{3} ../bin/{0} --min-width=0 --url={1} --out={2}".format(cutybin, domain_src_file, output_file, xvfb)

        print 'source html: ' + local_src_file
        print "output file: " + output_file
        print "cmd: " + cmd

        result = yield tornado.gen.Task(self.run_cmd_async, cmd)
        print "==========DONE=============="
        
        resp = {    'success' : True,
                    'error' : None,
                    'image_url' : '/static/render/' + filename + '.jpg'
               }
       
        self.finish(resp)

    def run_cmd_async(self, cmd, callback = None):
        p = self.application.settings.get('pool')
        p.apply_async(subprocess.call, [shlex.split(cmd)], callback = callback)

settings = {
    "static_path" : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "pool" : Pool(4),
    "queue" : Queue(),
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
