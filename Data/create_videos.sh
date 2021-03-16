
echo "----------" $(date) "----------" >> videoLog.txt
/usr/bin/time -o videoLog.txt -a -f "%C, Runtime: %E" python create_videos.py
/usr/bin/time -o videoLog.txt -a -f "%C, Runtime: %E" python concatenate_videos.py
/usr/bin/time -o videoLog.txt -a -f "%C, Runtime: %E" sh speed_up_video.sh 4 20 ./Videos/2021/03/merged-cropped.mp4 merged-cropped-4x.mp4
/usr/bin/time -o videoLog.txt -a -f "%C, Runtime: %E" sh speed_up_video.sh 8 20 ./Videos/2021/03/merged-cropped.mp4 merged-cropped-8x.mp4
/usr/bin/time -o videoLog.txt -a -f "%C, Runtime: %E" sh speed_up_video.sh 16 20 ./Videos/2021/03/merged-cropped.mp4 merged-cropped-16x.mp4
printf "\n" >> videoLog.txt