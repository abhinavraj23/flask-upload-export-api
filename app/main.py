import os
import datetime
import csv
import time
import enum
import uuid

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

UPLOAD_STATE = {}
file_upload = reqparse.RequestParser()

file_upload.add_argument("csv",
                        type=werkzeug.datastructures.FileStorage,
                        location='files',
                        required=True,
                        help="CSV File")

file_upload.add_argument("token",
                        type=str,
                        required=True,
                        help="Run a GET request to get a upload ticket")


upload_thread = {}

@api.route('/upload')
class Upload(Resource):
    @api.expect(file_upload)
    def post(self):
        args = file_upload.parse_args()
        global UPLOAD_STATE
        id = args["token"]
        if UPLOAD_STATE[id] == States.IN_PROGRESS:
            resp = jsonify({'message': 'Wait for upload to complete'})
            resp.status_code = 400
            return resp
        if args['csv'].mimetype == "text/csv":
            filename = str(datetime.datetime.now())
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            filestream = args['csv'].stream
            upload_thread[id].set()
            flag = 1
            UPLOAD_STATE[id] = States.IN_PROGRESS
            print("Uplaoding file...")
            with open(filepath, 'wb') as newfile:
                for line in filestream:
                    upload_thread[id].wait()
                    #ADDED MANUALLY FOR DEMO
                    time.sleep(0.5)
                    if(UPLOAD_STATE[id] == States.PAUSED):
                        while(UPLOAD_STATE[id] !=  States.IN_PROGRESS):
                            if(UPLOAD_STATE[id] == States.STOPPED):
                                break
                            pass
                    if UPLOAD_STATE[id] == States.STOPPED:
                        flag = 0
                        break
                    print(line, sep='')
                    newfile.write(line)
            if flag == 0:
                UPLOAD_STATE[id] = States.STOPPED
                os.remove(filepath)
                print("File upload was stopped")
                del UPLOAD_STATE[id]
                resp = jsonify({'message': 'File upload was stopped'})
                resp.status_code = 201
                return resp
            UPLOAD_STATE[id] = States.READY
            print("File uploaded")
            resp = jsonify({'message': 'File uploaded'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'message': 'A unkown error occured'})
            resp.status_code = 400
            return resp

@api.route('/upload/token')
class UploadToken(Resource):
    def get(self):
        global UPLOAD_STATE
        id = uuid.uuid1()
        UPLOAD_STATE[str(id.hex)] = States.READY
        upload_thread[str(id.hex)] = threading.Event()
        resp = jsonify({'token': str(id.hex)})
        resp.status_code = 200
        return resp

@api.route('/upload/status/<string:token>')
class UploadStatus(Resource):
    def get(self,token):
        global UPLOAD_STATE
        resp = jsonify({'status': (UPLOAD_STATE[token].value)})
        resp.status_code = 201
        return resp

@api.route('/upload/pause')
class PauseUpload(Resource):
    @api.expect(api.model('Token', {
        "token": fields.String,
    }))
    def post(self):
        global UPLOAD_STATE
        req = request.json
        id = req["token"]
        if UPLOAD_STATE[id] != States.IN_PROGRESS:
            print('Pause not required', UPLOAD_STATE[id].value)
            resp = jsonify({'message': 'Pause not required'})
            resp.status_code = 201
            return resp
        upload_thread[id].clear()
        UPLOAD_STATE[id] = States.PAUSED
        print(UPLOAD_STATE[id])
        resp = jsonify({'message': 'File upload paused'})
        resp.status_code = 201
        return resp

@api.route('/upload/resume')
class ResumeUpload(Resource):
    @api.expect(api.model('Token', {
        "token": fields.String,
    }))
    def post(self):
        global UPLOAD_STATE
        req = request.json
        id = req["token"]
        if UPLOAD_STATE[id] != States.PAUSED:
            print('Not required', UPLOAD_STATE[id].value)
            resp = jsonify({'message': 'Resume not required'})
            resp.status_code = 201
            return resp
        upload_thread[id].set()
        UPLOAD_STATE[id] = States.IN_PROGRESS
        print(UPLOAD_STATE[id])
        resp = jsonify({'message': 'File upload resumed'})
        resp.status_code = 201
        return resp

@api.route('/upload/stop')
class StopUpload(Resource):
    @api.expect(api.model('Token', {
        "token": fields.String,
    }))
    def delete(self):
        global UPLOAD_STATE
        req = request.json
        id = req["token"]
        if UPLOAD_STATE[id] != States.IN_PROGRESS and UPLOAD_STATE[id] != States.PAUSED:
            print('Stop not required', UPLOAD_STATE[id].value)
            resp = jsonify({'message': 'Already Stopped'})
            resp.status_code = 201
            return resp
        upload_thread[id].set()
        UPLOAD_STATE[id] = States.STOPPED
        print('Stopping')
        resp = jsonify({'message':'Stopping'})
        resp.status_code = 201
        return resp



############################ FOR EXPORT ###########################################

EXPORT_STATE = {}

export_thread = {}

@api.route('/export')
class Export(Resource):
    @api.expect(api.model('Query', {
        "rows": fields.Integer,
        "token": fields.String
    }))
    def post(self):
        req = request.json
        row = int(req['rows'])
        id = req["token"]
        lines = []
        global EXPORT_STATE
        if EXPORT_STATE[id] == States.IN_PROGRESS:
            resp = jsonify({'message': 'Wait for export to complete'})
            resp.status_code = 400
            return resp

        f = open(app.config["DATA_URL"], "r")
        export_thread[id].set()
        flag = 1
        EXPORT_STATE[id] = States.IN_PROGRESS
        for line in csv.reader(f):
            if row > 0:
                export_thread[id].wait
                row -= 1
                lines.append(line)
                if(EXPORT_STATE[id] == States.PAUSED):
                    while(EXPORT_STATE[id] !=  States.IN_PROGRESS):
                        if(EXPORT_STATE[id] == States.STOPPED):
                            break
                        pass
                if EXPORT_STATE[id] == States.STOPPED:
                    flag = 0
                    break
                #Artificial delay for demo
                time.sleep(0.5)
            else:
                break
        f.close()
        if flag == 0:
            EXPORT_STATE[id] = States.STOPPED
            print("File upload was stopped")
            resp = jsonify({'message': 'File export was stopped'})
            resp.status_code = 201
            return resp

        EXPORT_STATE[id] = States.READY
        print("Export completed")
        resp = jsonify({'message': lines})
        resp.status_code = 201
        return resp

@api.route('/export/token')
class ExportToken(Resource):
    def get(self):
        global EXPORT_STATE
        id = uuid.uuid1()
        EXPORT_STATE[str(id.hex)] = States.READY
        export_thread[str(id.hex)] = threading.Event()
        resp = jsonify({'token': str(id.hex)})
        resp.status_code = 200
        return resp

@api.route('/export/status/<string:token>')
class ExportStatus(Resource):
    def get(self,token):
        global EXPORT_STATE
        resp = jsonify({'status': (EXPORT_STATE[token].value)})
        resp.status_code = 201
        return resp

@api.route('/export/pause')
class PauseExport(Resource):
    @api.expect(api.model('Token', {
        "token": fields.String,
    }))
    def post(self):
        global EXPORT_STATE
        req = request.json
        id = req["token"]
        if EXPORT_STATE[id] != States.IN_PROGRESS:
            print('Pause not required', EXPORT_STATE[id].vallue)
            resp = jsonify({'message': 'Pause not required'})
            resp.status_code = 201
            return resp
        export_thread[id].clear()
        EXPORT_STATE[id] = States.PAUSED
        print(EXPORT_STATE[id].value)
        resp = jsonify({'message': 'File export paused'})
        resp.status_code = 201
        return resp

@api.route('/export/resume')
class ResumeExport(Resource):
    @api.expect(api.model('Token', {
        "token": fields.String,
    }))
    def post(self):
        global EXPORT_STATE
        req = request.json
        id = req["token"]
        if EXPORT_STATE[id] != States.PAUSED:
            print('Not required', EXPORT_STATE[id].value)
            resp = jsonify({'message': 'Resume not required'})
            resp.status_code = 201
            return resp
        export_thread[id].set()
        EXPORT_STATE[id] = States.IN_PROGRESS
        print(EXPORT_STATE[id].value)
        resp = jsonify({'message': 'File export resumed'})
        resp.status_code = 201
        return resp

@api.route('/export/stop')
class StopExport(Resource):
    @api.expect(api.model('Token', {
        "token": fields.String,
    }))
    def delete(self):
        global EXPORT_STATE
        req = request.json
        id = req["token"]
        if EXPORT_STATE[id] != States.IN_PROGRESS and EXPORT_STATE[id] != States.PAUSED:
            print('Stop not required', EXPORT_STATE[id].value)
            resp = jsonify({'message': 'Already Stopped'})
            resp.status_code = 201
            return resp
        export_thread[id].set()
        EXPORT_STATE[id] = States.STOPPED
        print('Stopping')
        resp = jsonify({'message':'Stopping'})
        resp.status_code = 201
        return resp



