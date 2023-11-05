# Blob Api

## Description

This is a simple api to store and retrieve blobs.
In BlobApi folder there is the server, with all the endpoints, the blob_service, which is the service that manages the blobs, and the database, which is a simple json file.
The files are stored locally in the server, in the folder "storage", which can be changed with the params.

The cli folder contains a simple cli to interact with the api.
In the shell there is a CMD shell implementation. With all the commands useful for the api.
The blobservice and the blob files are the client Library to call the endpoints.

## Installation

Use [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip install -r requirements.txt 
```

There could be some problems with the installation of the package "adiauthcli", for example my pipeline in github actions fails because of that, so if you have problems with that, just install the package manually.

## Usage
The Shell can be used with interactive commands or can be used a Script file.
To use the interactive shell, just run the cli.py file, and the shell will start.
To use the script file use the option SCRIPT and the path of the script file.

All the endpoints are documented with swagger, and can be accessed in the url: http://localhost:3002 or other port if you change it.


[Swagger](https://uclm-esi-necula.github.io/AppDistInt/)