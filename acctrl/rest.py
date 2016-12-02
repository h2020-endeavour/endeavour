from flask import Flask, url_for, Response, json, request

class AccessControlApp(object):

    def __init__(self, access_control):
        self.app = Flask(__name__)
        self.app.access_control = access_control
        self.setup()

    def setup(self):

        @self.app.route('/access_control', methods = ['POST'])
        def api_access_control():
            data = request.json
            if request.headers['Content-Type'] == 'application/json':
                success = self.app.access_control.process_access_control_flows(data)
                return self.handle_response(success, data)
            else:
                return Response("Unsupported media type\n" + data, status=415)


    def handle_response(self, success, data):
        json_data = json.dumps(data)
        if success:
            return Response("OK\n" + json_data, status=200)
        else:
            return Response("BAD REQUEST\n" + json_data, status=400)
            