ffmpeg -i $2 -map 0:v -c:v copy -bsf:v h264_mp4toannexb raw.h264
ffmpeg -fflags +genpts -r $1*25 -i raw.h264 -c:v copy $3
rm raw.h264