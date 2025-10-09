FROM ros:humble-ros-core-jammy AS base
#FROM osrf/ros:humble-desktop-full AS base 

# Install all dependencies in one layer and clean up apt caches
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    python3 \
    python3-pip \
    python3-colcon-common-extensions \
    python3-colcon-mixin \
    python3-rosdep \
    python3-vcstool \
    vim \
    ros-humble-mavros \
    ros-humble-rosbag2 \
    ros-humble-ros2bag \
    ros-humble-rosbag2-storage-default-plugins \
    ros-humble-rosbag2-compression-zstd \
    wget \
    libblas-dev \
    liblapack-dev \
    libmetis-dev \
    gfortran \
    gpiod libgpiod-dev libgpiod2 \
    python3-libgpiod \
    meson \
    ninja-build \
    pkg-config \
    gcc \
    g++ \
    systemd && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install casadi pymavlink pyserial pyyaml pandas shapely matplotlib numba scipy

# GeographicLib datasets installation
RUN wget https://raw.githubusercontent.com/mavlink/mavros/master/mavros/scripts/install_geographiclib_datasets.sh && \
    chmod +x install_geographiclib_datasets.sh && \
    ./install_geographiclib_datasets.sh && \
    rm install_geographiclib_datasets.sh

# Set up the entrypoint
COPY ./docker/coinhsl-archive-2022.12.02.tar.gz /
COPY ./docker/coinhsl-archive-2022.12.02.zip /

RUN gunzip coinhsl-archive-2022.12.02.tar.gz && \
    tar xf coinhsl-archive-2022.12.02.tar && \
    mv coinhsl-archive-2022.12.02 coinhsl && \
    git clone https://github.com/coin-or-tools/ThirdParty-HSL.git && \
    mv coinhsl /ThirdParty-HSL/ && \
    cd ThirdParty-HSL && \
    ./configure -C && \
    make -j$(nproc-1) && \
    make install 

# Clone and build ThirdParty-HSL and mavlink-router
RUN git clone https://github.com/mavlink-router/mavlink-router.git && \
    cd mavlink-router && \
    git submodule update --init --recursive && \
    meson setup build . && \
    ninja -C build && \
    ninja -C build install && \
    cd /ThirdParty-HSL && \
    ./configure -C && \
    make -j$(nproc) && \
    make install

COPY ./docker/entrypoint.sh /
ENTRYPOINT [ "/entrypoint.sh" ]

## Development image
FROM base AS develop

SHELL ["/bin/bash", "-c"]

#Create an overlay workspace
RUN mkdir -p /develop_ws/src \
    && echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc 

WORKDIR /develop_ws/src

RUN cd /develop_ws/ \
    && colcon build --symlink-install \
    && source install/setup.bash  \
    && apt-get update && apt-get install -y tmux 

 # Set up the entrypoint
COPY ./docker/entrypoint.sh ./useful_shell_scripts/run_mavros_router.sh /
COPY ./useful_shell_scripts/run_live.sh /

# Will test to see if we can add our RUN commands after everything that already exists.

WORKDIR /develop_ws
# Copy your scripts into the container
COPY ./useful_shell_scripts/run_prepare_container.sh ./
COPY ./useful_shell_scripts/run_multisines.sh ./
COPY ./docker/entrypoint.sh ./

# Make scripts executable
RUN chmod +x run_prepare_container.sh run_multisines.sh entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]