#author Liduo Fang
#Short Tail Lab


from tornado.options import define, options, parse_command_line
from tornado import httpclient
from tornado.gen import Task, engine
import tornado.ioloop
import datetime
import tornado.web
import json,os.path
import time
import subprocess
define("port",default=8000,type=int)
global fid
fid=0

class convertHtmlHandler(tornado.web.RequestHandler):
    def get(self,*args,**kwargs):
        htmlcontent=self.get_argument('subject')
        #format file name
        global fid
        if (fid>99999):
            fid=0
        else:
            fid=fid+1
        now=datetime.datetime.now()
        filename=now.strftime("%Y%m%dT%H%M%S")+"F"+str(fid)
        print "====================="
        print "assgning filename and saveing file"
        f=open('../static/'+filename+'.html','w')
        f.write(htmlcontent)
        f.close()

        print "../static/"+filename+'.html written'

        print "====================="
        print "running HTML->IMG"
        print "filename:"+filename
        subprocess.call(["./../bin/wkhtmltoimage-i386","../static/"+filename+".html","../static/"+filename+".jpg"])
        print "====================="
        print "returning..."
        
        rtndict={'imgurl':'static/'+filename+'.jpg'}
        
        self.finish(rtndict);

#-------------------------------------------------------------------
#end of class implement
settings={  
            "debug" : True,
            "static_path" :"static" 
         }

apns_options={ 
    'dev' : {
        'certfile' : os.path.join(os.path.dirname(__file__), 'apns-draw-dev.pem'),
        'apns_host' : ( 'gateway.sandbox.push.apple.com', 2195 ),
        'feedback_host' : ( 'feedback.sandbox.push.apple.com', 2196 ),
        'apns_reconnect_lag' : 5,
        'feedback_reconnect_lag' : 30
    },
    'prod' : {
        'certfile' : os.path.join(os.path.dirname(__file__), 'apns-draw-prod.pem'),
        'apns_host' : ( 'gateway.push.apple.com', 2195 ),
        'feedback_host' : ( 'feedback.push.apple.com', 2196 ),
        'apns_reconnect_lag' : 5,
        'feedback_reconnect_lag' : 30
    }
}



application = tornado.web.Application([
    (r"^/convert",convertHtmlHandler ),
], **settings)

if __name__ == "__main__":
    parse_command_line()
    application.listen(int(options.port))
    tornado.ioloop.IOLoop.instance().start()
