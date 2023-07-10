from app.servicio_whatsapp import app
from gevent.pywsgi import WSGIServer
 
if __name__ == "__main__":
    http_server = WSGIServer(('0.0.0.0', 8080), app)
    http_server.serve_forever()
