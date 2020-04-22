import os
import datetime
import csv
import time
import enum

from flask import Flask, request, redirect, jsonify
from flask_restplus import Api, Resource, reqparse, abort, fields
import werkzeug

import threading

app = Flask(__name__)
api = Api(app)

class States(enum.Enum):
    READY = 'READY'
    IN_PROGRESS = 'IN PROGRESS'
    PAUSED = 'PAUSED'
    STOPPED  = 'STOPPED'
    COMPLETED = 'COMPLETED'

############################## FOR UPLOADING #########################################

UPLOAD_STATE = States.READY
file_upload = reqparse.RequestParser()

file_upload.add_argument("csv",
                        type=werkzeug.datastructures.FileStorage,
                        location='files',
                        required=True,
                        help="CSV File")


upload_thread = threading.Event()

@api.route('/upload')
class Upload(Resource):
    @api.expect(file_upload)
    def post(self):
        args = file_upload.parse_args()
        global UPLOAD_STATE
        if UPLOAD_STATE == States.IN_PROGRESS:
            resp = jsonify({'message': 'Wait for upload to complete'})
            resp.status_code = 400
            return resp
        if args['csv'].mimetype == "text/csv":
            filename = str(datetime.datetime.now())
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            filestream = args['csv'].stream
            upload_thread.set()
            flag = 1
            UPLOAD_STATE = States.IN_PROGRESS
            print("Uplaoding file...")
            with open(filepath, 'wb') as newfile:
                for line in filestream:
                    upload_thread.wait()
                    #ADDED MANUALLY FOR DEMO
                    time.sleep(0.5)
                    if(UPLOAD_STATE == States.PAUSED):
                        while(UPLOAD_STATE !=  States.IN_PROGRESS):
                            pass
                    if UPLOAD_STATE == States.STOPPED:
                        flag = 0
                        break
                    print(line, sep='')
                    newfile.write(line)
            if flag == 0:
                UPLOAD_STATE = States.STOPPED
                os.remove(filepath)
                print("File upload was stopped")
                resp = jsonify({'message': 'File upload was stopped'})
                resp.status_code = 201
                return resp
            UPLOAD_STATE = States.READY
            print("File uploaded")
            resp = jsonify({'message': 'File uploaded'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'message': 'A unkown error occured'})
            resp.status_code = 400
            return resp

@api.route('/upload/status')
class UploadStatus(Resource):
    def get(self):
        global UPLOAD_STATE
        resp = jsonify({'status': (UPLOAD_STATE.value)})
        resp.status_code = 201
        return resp

@api.route('/upload/pause')
class PauseUpload(Resource):
    def get(self):
        global UPLOAD_STATE
        if UPLOAD_STATE != States.IN_PROGRESS:
            print('Pause not required', UPLOAD_STATE)
            resp = jsonify({'message': 'Pause not required'})
            resp.status_code = 201
            return resp
        upload_thread.clear()
        UPLOAD_STATE = States.PAUSED
        print(UPLOAD_STATE)
        resp = jsonify({'message': 'File upload paused'})
        resp.status_code = 201
        return resp

@api.route('/upload/resume')
class ResumeUpload(Resource):
    def get(self):
        global UPLOAD_STATE
        if UPLOAD_STATE != States.PAUSED:
            print('Not required', UPLOAD_STATE)
            resp = jsonify({'message': 'Resume not required'})
            resp.status_code = 201
            return resp
        upload_thread.set()
        UPLOAD_STATE = States.IN_PROGRESS
        print(UPLOAD_STATE)
        resp = jsonify({'message': 'File upload resumed'})
        resp.status_code = 201
        return resp

@api.route('/upload/stop')
class StopUpload(Resource):
    def get(self):
        global UPLOAD_STATE
        if UPLOAD_STATE != States.IN_PROGRESS and UPLOAD_STATE != States.PAUSED:
            print('Stop not required', UPLOAD_STATE)
            resp = jsonify({'message': 'Already Stopped'})
            resp.status_code = 201
            return resp
        upload_thread.set()
        UPLOAD_STATE = States.STOPPED
        print('Stopping')
        resp = jsonify({'message':'Stopping'})
        resp.status_code = 201
        return resp



############################ FOR EXPORT ###########################################

EXPORT_STATE = States.READY

export_thread = threading.Event()

@api.route('/export')
class Export(Resource):
    @api.expect(api.model('Query', {
        "rows": fields.Integer,
    }))
    def post(self):
        req = request.json
        row = int(req['rows'])
        lines = []
        global EXPORT_STATE
        if EXPORT_STATE == States.IN_PROGRESS:
            resp = jsonify({'message': 'Wait for export to complete'})
            resp.status_code = 400
            return resp

        f = open(app.config["DATA_URL"], "r")
        export_thread.set()
        flag = 1
        EXPORT_STATE = States.IN_PROGRESS
        for line in csv.reader(f):
            if row > 0:
                export_thread.wait
                row -= 1
                lines.append(line)
                if(EXPORT_STATE == States.PAUSED):
                    while(EXPORT_STATE !=  States.IN_PROGRESS):
                            pass
                if EXPORT_STATE == States.STOPPED:
                    flag = 0
                    break
                #Artificial delay for demo
                time.sleep(0.5)
            else:
                break
        f.close()
        if flag == 0:
            EXPORT_STATE = States.STOPPED
            print("File upload was stopped")
            resp = jsonify({'message': 'File export was stopped'})
            resp.status_code = 201
            return resp

        EXPORT_STATE = States.READY
        print("File uploaded")
        resp = jsonify({'message': lines})
        resp.status_code = 201
        return resp

@api.route('/export/status')
class ExportStatus(Resource):
    def get(self):
        global EXPORT_STATE
        resp = jsonify({'status': (EXPORT_STATE.value)})
        resp.status_code = 201
        return resp

@api.route('/export/pause')
class PauseExport(Resource):
    def get(self):
        global EXPORT_STATE
        if EXPORT_STATE != States.IN_PROGRESS:
            print('Pause not required', EXPORT_STATE.vallue)
            resp = jsonify({'message': 'Pause not required'})
            resp.status_code = 201
            return resp
        export_thread.clear()
        EXPORT_STATE = States.PAUSED
        print(EXPORT_STATE.value)
        resp = jsonify({'message': 'File export paused'})
        resp.status_code = 201
        return resp

@api.route('/export/resume')
class ResumeExport(Resource):
    def get(self):
        global EXPORT_STATE
        if EXPORT_STATE != States.PAUSED:
            print('Not required', EXPORT_STATE.value)
            resp = jsonify({'message': 'Resume not required'})
            resp.status_code = 201
            return resp
        export_thread.set()
        EXPORT_STATE = States.IN_PROGRESS
        print(EXPORT_STATE.value)
        resp = jsonify({'message': 'File export resumed'})
        resp.status_code = 201
        return resp

@api.route('/export/stop')
class StopExport(Resource):
    def get(self):
        global EXPORT_STATE
        if EXPORT_STATE != States.IN_PROGRESS and EXPORT_STATE != States.PAUSED:
            print('Stop not required', EXPORT_STATE.value)
            resp = jsonify({'message': 'Already Stopped'})
            resp.status_code = 201
            return resp
        export_thread.set()
        EXPORT_STATE = States.STOPPED
        print('Stopping')
        resp = jsonify({'message':'Stopping'})
        resp.status_code = 201
        return resp



