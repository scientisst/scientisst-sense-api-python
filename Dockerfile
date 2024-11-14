FROM ubuntu:jammy-20240911.1

# Install dependencies for pycairo, pyobject and pydbus
RUN apt update
RUN apt install -y python3.10
RUN apt install -y python3-pip
RUN apt install -y wget
RUN apt install -y libcairo2-dev libxt-dev libgirepository1.0-dev
RUN apt install -y build-essential libdbus-glib-1-dev libgirepository1.0-dev
RUN apt install -y ninja-build patchelf bluez dbus bluetooth

# Start bluetooth services
RUN service dbus start
RUN service bluetooth start

# Copy requirements file and install python requirements
COPY requirements.txt ./
RUN pip3 install meson
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy all files to container
COPY . .
