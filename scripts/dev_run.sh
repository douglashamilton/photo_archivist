#!/bin/bash

uvicorn src.photo_archivist.app:app --host 127.0.0.1 --port 8787 --reload



#Start-Process "http://127.0.0.1:8787/health"