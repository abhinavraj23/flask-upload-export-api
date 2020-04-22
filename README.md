 # Flask Upload/Export API

Flask file upload/export API with pause, resume and stop capability.
Endpoints:
  - /
  - /upload POST - For uploading a file
  - /export POST - For exporting rows through the given csv file
  - (upload or export)/pause GET - For pausing the upload/export of the file
  - (upload or export)/stop GET - For stopping the upload/export of the file
  - (upload or export)/resume GET - For resuming the paused upload/export of the file
  - (upload or export)/status GET - For getting the upload/export status of the file

#### Running image :
Build the docker image from here or from [DockerHub] (https://hub.docker.com/repository/docker/abhinavraj23/flask-upload-export-api) for testing.