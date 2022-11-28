# Use Ubuntu
FROM ubuntu:18.04

# Add Python repository
FROM python:3.11-slim-bullseye

# Add dependencies required by PySide6
RUN apt-get update -y && apt-get install libxcb-xinerama0 libglib2.0-0 ffmpeg libsm6 libxext6 freeglut3 freeglut3-dev -y

# Add git so PyTest does not complain
RUN apt-get install -y git

# Copy the repository
COPY . ./foundry

# Download dependencies
RUN pip install -r foundry/requirements-dev.txt
