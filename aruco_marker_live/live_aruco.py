import cv2
import time
import pickle
import numpy as np


def live_aruco_detection(calibration_data):
    """
    실시간으로 비디오를 받아 ArUco 마커를 검출하고 3D 포즈를 추정하는 함수

    Args:
        calibration_data: 카메라 캘리브레이션 데이터를 포함한 딕셔너리
            - camera_matrix: 카메라 내부 파라미터 행렬
            - dist_coeffs: 왜곡 계수
    """
    # 캘리브레이션 데이터 추출
    camera_matrix = calibration_data['camera_matrix']
    dist_coeffs = calibration_data['dist_coeffs']

    # ArUco 검출기 설정
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

    # 마커 크기 설정 (미터 단위)
    marker_size = 0.07  # 예: 7cm = 0.07m

    # 카메라 설정
    cap = cv2.VideoCapture(0)

    # 카메라 초기화 대기
    if not cap.isOpened():
        print("❌ Error: Cannot open camera")
        return

    print("✅ Camera opened successfully")
    time.sleep(1)

    # FPS 및 latency 계산을 위한 변수
    fps = 0
    frame_count = 0
    fps_start_time = time.time()

    while True:
        # latency 측정 시작
        loop_start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # 이미지 왜곡 보정
        frame_undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)

        # 마커 검출
        corners, ids, rejected = detector.detectMarkers(frame_undistorted)

        # 마커가 검출되면 표시 및 포즈 추정
        if ids is not None:
            # 검출된 마커 표시
            cv2.aruco.drawDetectedMarkers(frame_undistorted, corners, ids)

            # 각 마커에 대해 처리
            for i in range(len(ids)):
                # 3D 객체 포인트 정의 (마커의 네 모서리)
                # 마커 중심을 원점으로 하는 좌표계
                half_size = marker_size / 2
                obj_points = np.array([
                    [-half_size, half_size, 0],
                    [half_size, half_size, 0],
                    [half_size, -half_size, 0],
                    [-half_size, -half_size, 0]
                ], dtype=np.float32)

                # 각 마커의 포즈 추정 (solvePnP 사용)
                success, rvec, tvec = cv2.solvePnP(
                    obj_points,
                    corners[i],
                    camera_matrix,
                    dist_coeffs,
                    flags=cv2.SOLVEPNP_IPPE_SQUARE
                )

                if not success:
                    continue

                # 좌표축 표시
                cv2.drawFrameAxes(frame_undistorted, camera_matrix, dist_coeffs,
                                  rvec, tvec, marker_size/2)

                # 마커의 3D 위치 표시
                pos_x = tvec[0][0]
                pos_y = tvec[1][0]
                pos_z = tvec[2][0]

                # 회전 벡터를 오일러 각도로 변환
                rot_matrix, _ = cv2.Rodrigues(rvec)
                euler_angles = cv2.RQDecomp3x3(rot_matrix)[0]

                # 마커 정보 표시
                corner = corners[i][0]
                center_x = int(np.mean(corner[:, 0]))
                center_y = int(np.mean(corner[:, 1]))

                cv2.putText(frame_undistorted,
                            f"ID: {ids[i][0]}",
                            (center_x, center_y - 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)

                cv2.putText(frame_undistorted,
                            f"Pos: ({pos_x:.2f}, {pos_y:.2f}, {pos_z:.2f})m",
                            (center_x, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)

                cv2.putText(frame_undistorted,
                            f"Rot: ({euler_angles[0]:.1f}, {euler_angles[1]:.1f}, {euler_angles[2]:.1f})deg",
                            (center_x, center_y + 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 2)

                # 코너 포인트 표시
                for point in corner:
                    x, y = int(point[0]), int(point[1])
                    cv2.circle(frame_undistorted, (x, y), 4, (0, 0, 255), -1)

        # FPS 및 latency 계산
        frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - fps_start_time

        # 매 초마다 FPS 업데이트
        if elapsed_time >= 1.0:
            fps = frame_count / elapsed_time
            frame_count = 0
            fps_start_time = current_time

        # latency 계산 (milliseconds)
        latency = (time.time() - loop_start_time) * 1000

        # FPS와 latency 표시
        cv2.putText(frame_undistorted,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

        cv2.putText(frame_undistorted,
                    f"Latency: {latency:.1f}ms",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

        cv2.putText(frame_undistorted,
                    f"Press 'q' to quit",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

        # 프레임 표시
        cv2.imshow('ArUco Marker Detection', frame_undistorted)

        # 'q' 키를 누르면 종료
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' 또는 ESC
            break

    # 리소스 해제
    cap.release()
    cv2.destroyAllWindows()


def get_default_calibration(width=1280, height=720):
    """
    기본 카메라 캘리브레이션 파라미터 생성
    일반적인 웹캠의 대략적인 값을 사용
    """
    # 대략적인 focal length 계산 (픽셀 기준)
    fx = fy = width  # 대략적인 추정값
    cx = width / 2
    cy = height / 2

    camera_matrix = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ], dtype=np.float32)

    # 왜곡 계수 (왜곡 없음으로 가정)
    dist_coeffs = np.zeros((5, 1), dtype=np.float32)

    return {
        'camera_matrix': camera_matrix,
        'dist_coeffs': dist_coeffs
    }


def main():
    # 캘리브레이션 데이터 로드
    try:
        with open('camera_calibration.pkl', 'rb') as f:
            calibration_data = pickle.load(f)
        print("✅ Calibration data loaded successfully")
    except FileNotFoundError:
        print("⚠️ Camera calibration file not found. Using default calibration parameters...")
        calibration_data = get_default_calibration()
    except Exception as e:
        print(f"⚠️ Error loading calibration data: {e}")
        print("Using default calibration parameters...")
        calibration_data = get_default_calibration()

    print("Starting ArUco marker detection...")
    print("Press 'q' to quit")
    live_aruco_detection(calibration_data)


if __name__ == "__main__":
    main()
