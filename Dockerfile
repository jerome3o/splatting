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

ARG CUDA_ARCHITECTURES=75;89

RUN git clone https://github.com/colmap/colmap.git
RUN mkdir -p colmap/build
# TODO: parameterise architecture
RUN cd colmap/build && cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES}
RUN cd colmap/build && ninja
RUN cd colmap/build && ninja install

RUN apt install wget ffmpeg libglm-dev -y \
  && rm -rf /var/lib/apt/lists/*

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
  && echo "634d76df5e489c44ade4085552b97bebc786d49245ed1a830022b0b406de5817 Miniconda3-latest-Linux-x86_64.sh" | sha256sum --check

RUN bash ./Miniconda3-latest-Linux-x86_64.sh -b

RUN conda init

WORKDIR /splatting/

COPY ./gaussian-splatting/environment.yml .
COPY ./gaussian-splatting/submodules/ submodules/

# I assume this is the name as the CUDA_ARCHITECTURES except /10. The ARG should be used here
# Values taken from https://github.com/pytorch/extension-cpp/issues/71#issuecomment-1183674660
ENV TORCH_CUDA_ARCH_LIST="3.5;5.0;6.0;6.1;7.0;7.5;8.0;8.6+PTX"
RUN conda env create --file environment.yml

ENV PATH=/opt/conda/envs/gaussian_splatting:/splatting:${PATH}

RUN echo "conda activate gaussian_splatting" >> ~/.bashrc
# SHELL ["/bin/bash", "--login", "-c"]


# TODO: move to main apt calls

RUN apt update && apt install imagemagick -y

COPY ./gaussian-splatting/. ./



## Dagsters specific - TODO(j.swannack): should be a different image
WORKDIR /dagster/

# scuffed combination of pip and conda environments
COPY requirements.txt .

RUN pip install -r requirements.txt

ENV SPLAT_PYTHON_INTERPRETER=/opt/conda/envs/gaussian_splatting/bin/python \
  SPLAT_DIR=/splatting/

COPY dagster.yaml .
COPY dagsplat/ dagsplat/
RUN mkdir .dagster_home
RUN cp /dagster/dagster.yaml /dagster/.dagster_home/dagster.yaml

CMD ["dagster", "dev", "-m", "dagsplat", "--host", "0.0.0.0"]
