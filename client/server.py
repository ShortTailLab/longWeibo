import datetime, time
import json
import subprocess
import random
import cStringIO
from PIL import Image
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path 
from tornado.options import define, options, parse_command_line

define("port", default=8001, help="run on the given port", type=int)
define("i386", default=False, help="use this option if running on 32bit system", type=bool)
define("xvfb", default=False, help="use this option if running on headless server", type=bool)

RAND_FILE_NAME_LENGTH = 12

cutybin = ""
xvfb = ""

def file_path(relative) :
    pyabspath = os.path.abspath(__file__)
    abspath=os.path.dirname(pyabspath)
    relative='./'+relative
    path=os.path.join(abspath,relative)
    return path

def domain_path(relative) :
    return os.path.join('http://localhost:8000', relative)

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

        iname, iext = os.path.splitext(f['filename'])
        if iext == "" or iext.lower() not in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif']:
            self.finish("Wrong file type")
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
            'name' : filename,
            'size' : size,
            'url'  : '/static/uploads/' + filename,
            'thunmnail_url' : '/static/uploads/' + filename,
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
        #global fid
        #if (fid>99999):
        #    fid=0
        #else:
        #    fid=fid+1
        #now=datetime.datetime.now()
        #filename = now.strftime("%Y%m%dT%H%M%S") + "F" + str(fid)
        filename = rand_string()

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
        cmd = "{3} ./../bin/{0} --min-width=0 --url={1} --out={2}".format(cutybin, domain_src_file, output_file, xvfb)
        print "cmd: " + cmd
        subprocess.Popen(cmd, shell=True)
        print "==========END=============="
        
        resp = {    'success' : True,
                    'error' : None,
                    'image_url' : '/static/render/' + filename + '.jpg'
                }
       
        self.finish( resp )

class deleteImage(tornado.web.RequestHandler):
    def get(self,*args,**kwargs):
        imagePath=self.get_argument("imagePath");
        imageAbsPath=file_path(imagePath)
        print "removing: "+imageAbsPath
        os.remove(imageAbsPath)
        self.finish(
        {
            'success':True,
            'error':None},
        )






settings ={
    "static_path" : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
}


application = tornado.web.Application([
    (r"/", Home),
    (r"/upload", UploadImage),
    (r"/render", Render),
    (r"/deleteImage",deleteImage),
], **settings);

if __name__ == "__main__":
    parse_command_line()
    cutybin = "CutyCapt-i686" if options.i386 else "CutyCapt-x64"
    xvfb = "xvfb-run --server-args=\"-screen 1, 1024x768x24\"" if options.xvfb else ""

    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
