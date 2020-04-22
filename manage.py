from app.main import app

import os
import errno

if __name__ == "__main__":
    UPLOAD_FOLDER = './app/static'
    DATA_URL = './app/static/data.csv'

    app.secret_key = "secret key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config["DATA_URL"] = DATA_URL
    try:
        os.makedirs(UPLOAD_FOLDER)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 * 1024
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)