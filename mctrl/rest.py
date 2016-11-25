from flask import Flask, url_for, Response, json, request

class MonitorApp(object):

    def __init__(self, monitor):
        self.app = Flask(__name__)
        self.app.monitor = monitor
        self.setup()

    def setup(self):
        @self.app.route('/anomaly', methods = ['POST'])
        def api_anomaly():
            data = request.json
            if request.headers['Content-Type'] == 'application/json':
                success = self.app.monitor.process_anomaly_data(data) 
                return self.handle_response(success, data)
            else:
                return Response("Unsupported media type\n" + data, status=415)

        @self.app.route('/monitor', methods = ['POST'])
        def api_monitor():
            data = request.json
            if request.headers['Content-Type'] == 'application/json':
                success = self.app.monitor.process_monitor_flows(data) 
                return self.handle_response(success, data)
            else:
                return Response("Unsupported media type\n" + data, status=415)


    def handle_response(self, success, data):
        json_data = json.dumps(data)
        if success:
            return Response("OK\n" + json_data, status=200)
        else:
            return Response("BAD REQUEST\n" + json_data, status=400)
            