set -euxo pipefail

DATA_DIR=/data/

# check for FRAME_RATE
if [[ -z "${FRAME_RATE}" ]]; then
  FRAME_RATE=6
fi

# Check if 'VIDEO_FILE' Variable is already defined
if [[ -z "${VIDEO_FILE}" ]]; then
    # If 'VIDEO_FILE' Is not defined, find the video file

    # Define the video extensions to look for
    video_extensions=("mp4" "mkv" "flv" "mov" "avi" "MOV")

    # Loop over the video extensions
    for ext in "${video_extensions[@]}"; do
        # Find the first video file of the given extension
        VIDEO_FILE=$(find "$DATA_DIR" -type f -name "*.$ext" | head -n 1)

        # If a video file is found, break the loop
        if [[ -n "$VIDEO_FILE" ]]; then
            break
        fi
    done
fi

FILE_NAME=$(basename $VIDEO_FILE)
# (
#   cd $DATA_DIR
#   /bin/ffmpeg -i $FILE_NAME -qscale:v 1 -qmin 1 -vf fps=$FRAME_RATE %04d.jpg
#   mkdir -p input
#   mv *.jpg input
# )

python convert.py -s $DATA_DIR
python train.py -s $DATA_DIR
