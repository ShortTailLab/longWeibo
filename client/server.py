import datetime, time, json, subprocess
import random, cStringIO, shlex
from multiprocessing import Pool, Queue
from PIL import Image
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, tornado.gen
from tornado.options import define, options, parse_command_line
import os.path 
import redis
from session import Session, RedisSessionStore

define("port", default=8000, help="run on the given port", type=int)
define("i386", default=False, help="use this option if running on 32bit system", type=bool)
define("xvfb", default=False, help="use this option if running on headless server", type=bool)
define("maxupload", default=2048, help="max uploaded image size, kb", type=bool)
define("debug", default=True, help="running server in debug mode", type=bool)
define("pc", default=4, help="number of subprocesses", type=int)
RAND_FILE_NAME_LENGTH = 12

# global stuff
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
R = redis.Redis(connection_pool = redis_pool)
sessionStore = RedisSessionStore(R)

# helper methods
def file_path(relative) :
    pyabspath = os.path.abspath(__file__)
    abspath = os.path.dirname(pyabspath)
    relative = './' + relative
    path = os.path.join(abspath,relative)
    return path

templateLoader = tornado.template.Loader(file_path(""))

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
    im.save(out_path, 'JPEG', quality = 95)

def find_template(name):
    if options.debug:
        global templateLoader
        templateLoader = tornado.template.Loader( file_path("") )
    return templateLoader.load(name)

# Handlers
class BaseHandler(tornado.web.RequestHandler):
    def session(self):
        sessionid = self.get_secure_cookie('session')
        return Session(sessionStore, sessionid) if sessionid else None

# Page
class Home(BaseHandler):
    def get(self):
        session = self.session()
        if session:
            session.access(self.request.remote_ip)
        else:
            session = Session(sessionStore)
            self.set_secure_cookie('session', value = session.sessionid)

        self.render(file_path("index.html"))

# Json
class UploadImage(BaseHandler):
    def post(self):
        f = self.request.files[u'files[]'][0]

        # limit upload file size
        filesize = len(f['body'])
        if filesize > (options.maxupload * 1024):
            self.send_error()
            return 
        
        # check file extension
        iname, iext = os.path.splitext(f['filename'])
        if iext == "" or iext.lower() not in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif']:
            self.send_error({ 'name' : filename, 'size' : size, 'success' : False })
            return

        # obtain a random file name
        filename = rand_string() + iext

        # save file to user session
        sid = self.get_secure_cookie('session')
        session = None
        if sid:
            session = Session(sessionStore, sessionid = sid)
        else: 
            session = Session(sessionStore)

        # store updated upload list to redis
        session.access(self.request.remote_ip)
        uploaded = session.uploaded()
        uploaded.append(filename)
        session.setUploaded(uploaded)

        print session.fetch('uploaded')

        # resize to a thumbnail then save to disk
        upload_path = file_path("static/uploads/") + filename
        save_thumbnail(f['body'], upload_path)

        resp = { 
            'success' : True,
            'name' : filename,
            'size' : filesize,
            'url'  : '/static/uploads/' + filename,
            'thunmnail_url' : '/static/uploads/' + filename,
            'delete_url' : '',
            'delete_type' : 'DELETE',
        }

        self.finish(resp)


# Json
class Render(BaseHandler):
    
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self,*args,**kwargs):
        itemList = json.loads(self.get_argument('itemList'))
        print str(itemList)

        
        itemHTML = ""
        for item in itemList:
            if item['type'] == 'text':
                itemHTML += find_template('_text_item.html').generate(text = item['text'], height = item['height'], style=item['style'])
            elif item['type'] == 'image':
                itemHTML += find_template('_image_item.html').generate(image_url = item['image_url'], width = item['width'])

        html = find_template("_render.html").generate( content = itemHTML )

        filename = rand_string()
        domain_src_file = domain_path('static/render/' + filename + '.html')
        local_src_file = file_path('static/render/' + filename + '.html')
        output_file = file_path('static/render/' + filename + '.jpg')

        print "=========RENDER FILE======="
        f = open(local_src_file,'w')
        f.write(html)
        f.close()
	
        cutybin = file_path("../bin/") + ("CutyCapt-i686" if options.i386 else "CutyCapt-x64")
    	xvfb = 'xvfb-run --auto-servernum --server-args="-screen 0, 1024x768x24"' if options.xvfb else ""
        cmd = "{3} {0} --min-width=0 --url={1} --out={2}".format(cutybin, domain_src_file, output_file, xvfb)

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

class DeleteImage(tornado.web.RequestHandler):
    def get(self,*args,**kwargs):
        imagePath=self.get_argument("imagePath");
        imageAbsPath=file_path(imagePath)
        print "removing: "+imageAbsPath
        os.remove(imageAbsPath)
        self.finish( { 'success':True,  'error':None} )

if __name__ == "__main__":
    parse_command_line()

    settings = {
        "static_path" : os.path.join(os.path.dirname(__file__), "static"),
        "debug" : True,
        "pool" : Pool(options.pc),
        "queue" : Queue(),
        "cookie_secret" : 'thisisacookiesecrethahaha'
    }

    application = tornado.web.Application([
        (r"/", Home),
        (r"/upload", UploadImage),
        (r"/render", Render),
        (r"/deleteImage",DeleteImage),
    ], **settings);

    print "-----------------------------------------------"
    print "server started. port: {0}, debug: {1}, xvfb: {2}, process count: {3}".format(options.port, options.debug, options.xvfb, options.pc)
    print "-----------------------------------------------"
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
