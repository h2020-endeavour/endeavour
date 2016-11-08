from flask import Flask, url_for, Response, json, request

class MonitorApp(object):

    def __init__(self, monitor):
        self.app = Flask(__name__)
        self.app.monitor = monitor
        self.setup()

    def setup(self):
        @self.app.route('/anomaly', methods = ['POST'])
        def api_anomaly():
            data = json.dumps(request.json)
            if request.headers['Content-Type'] == 'application/json':
                return Response("OK\n" + data, status=200)
            else:
                return Response("Unsupported media type\n" + data, status=415)

