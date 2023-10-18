FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel

ENV TZ=Pacific/Auckland \
  DEBIAN_FRONTEND=noninteractive

# Build colmap
RUN apt-get update \
    && apt-get install -y \
    git \
    cmake \
    ninja-build \
    build-essential \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libceres-dev

RUN git clone https://github.com/colmap/colmap.git
RUN mkdir -p colmap/build
# TODO: parameterise architecture
RUN cd colmap/build && cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES=75
RUN cd colmap/build && ninja
RUN cd colmap/build && ninja install

RUN apt install wget ffmpeg libglm-dev -y \
  && rm -rf /var/lib/apt/lists/*

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
  && echo "634d76df5e489c44ade4085552b97bebc786d49245ed1a830022b0b406de5817 Miniconda3-latest-Linux-x86_64.sh" | sha256sum --check

RUN bash ./Miniconda3-latest-Linux-x86_64.sh -b

RUN conda init

WORKDIR /splatting/

COPY environment.yml .
COPY submodules/ submodules/

ENV TORCH_CUDA_ARCH_LIST="3.5;5.0;6.0;6.1;7.0;7.5;8.0;8.6+PTX"
RUN conda env create --file environment.yml

RUN echo "conda activate gaussian_splatting" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

COPY ./ ./

ENV PYTHONPATH=.

CMD ["./process.sh"]
