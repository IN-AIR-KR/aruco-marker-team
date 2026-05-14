# MediaMTX와 Gstreamer를 활용한 영상 스트리밍

## 하드웨어 가속 x

- MediaMTX
```bash
cd ~/Workspace/aruco_team/mediamtx_v1.16.3_linux_arm64
./mediamtx
```

- Gstreamer 송신
    - latency = 2.4~5

        ```bash
        gst-launch-1.0 v4l2src device=/dev/video0 ! \
            video/x-raw, width=640, height=480, framerate=30/1 ! \
            videoconvert ! \
            x264enc tune=zerolatency bitrate=2000 \
            speed-preset=ultrafast ! \
            h264parse ! \
            video/x-h264, stream-format=avc, alignment=au ! \
            rtspclientsink location=rtsp://127.0.0.1:8554/mystream
        ```
    - latency = 100ms 이하

        ```bash
        gst-launch-1.0 v4l2src device=/dev/video0 ! \
            video/x-raw, width=640, height=480, framerate=30/1 ! \
            videoconvert ! \
            openh264enc bitrate=2000000 ! h264parse ! \
            rtspclientsink \
            location=rtsp://127.0.0.1:8554/mystream

        ```

- Gstreamer 수신
    ```bash
    gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/mystream \
        protocols=tcp latency=100 ! \
        rtph264depay ! \
        h264parse ! \
        avdec_h264 ! \
        videoconvert ! \
        autovideosink
    ```

- 다른 기기에서 확인하는 법
    - 젯슨에서 `hostname -I`로 IP 주소 확인
    - 다른 기기에서 이 주소로 ping 날려서 연결되는지 확인
        - 시스쿨 와이파이로는 연결 안 됨. 핫스팟만 가능.
    - 다른 기기에서 VLC, Gstreamer 등 이용해서 rtsp://<JETSON_IP>:8554/mystream 연결해서 영상 수신되는지 확인

## Talescale setting


## TODO
- ~~기본 송수신 테스트~~
- 하드웨어 가속 사용
- 지연시간 최적화
- AruCo Marker, 객체 박스 등 overlay 해서 송출하는 파이프라인 구축