import os
import cv2
import time
import json
import subprocess
import numpy as np
from datetime import datetime
from multiprocessing import Process, Queue
from pyorbbecsdk import *
import tkinter
from tkinter import messagebox
import av

def display_images(display_queue: Queue, depth_height_threshold: int):
    """
    display captured images

    Args:
        display_queue (multiprocessing.queues.Queque): the data stream from the camera to be displayed
    """
    max_data = 5500
    while True:
        data = display_queue.get()
        if len(data) == 0:
            cv2.destroyAllWindows()
            break
        else:
            ir, depth = data
            ir = np.clip(ir + 100, 160, max_data)
            ir = np.clip(((np.log(ir) - 5) * 70), 0, None)
            try:
                depth = np.median(depth[depth > 0]) - depth
            except Exception:
                depth = np.median(depth) - depth
            depth = np.where((depth < 0) | (depth > depth_height_threshold), 0, depth)

            ir = (ir / ir.max() * 255).astype(np.uint8)
            depth = (depth / depth.max() * 255).astype(np.uint8)

            cv2.imshow("Infrared + depth streams", np.hstack((ir, depth)))
            cv2.waitKey(1)
        # clear queue before next iteration
        while True:
            try:
                display_queue.get_nowait()
            except:
                break


def write_frames(
    filename,
    frames,
    threads=6,
    fps=30,
    crf=10,
    pixel_format="gray8",
    codec="h264",
    close_pipe=True,
    pipe=None,
    slices=24,
    slicecrc=1,
    frame_size=None,
    get_cmd=False,
):
    """
    Write frames to avi file using the ffv1 lossless encoder

    Args:
        filename (str): path to the file to write the frames to.
        frames (numpy.ndarray): frames to write to file
        threads (int, optional): the number of threads for multiprocessing. Defaults to 6.
        fps (int, optional): camera frame rate. Defaults to 30.
        crf (int, optional): constant rate factor for ffmpeg, a lower value leads to higher quality. Defaults to 10.
        pixel_format (str, optional): pixel format for ffmpeg. Defaults to 'gray8'.
        codec (str, optional): codec option for ffmpeg. Defaults to 'h264'.
        close_pipe (bool, optional): boolean flag for closing ffmpeg pipe. Defaults to True.
        pipe (subprocess.pipe, optional): ffmpeg pipe for writing the video. Defaults to None.
        slices (int, optional): number of slicing in parallel encoding. Defaults to 24.
        slicecrc (int, optional): protect slices with cyclic redundency check. Defaults to 1.
        frame_size (str, optional): size of the frame, ie 640x576. Defaults to None.
        get_cmd (bool, optional): boolean flag for outputtting ffmpeg command. Defaults to False.

    Returns:
        pipe (subprocess.pipe, optional): ffmpeg pipe for writing the video.
    """

    # we probably want to include a warning about multiples of 32 for videos
    # (then we can use pyav and some speedier tools)

    if not frame_size and type(frames) is np.ndarray:
        frame_size = "{0:d}x{1:d}".format(frames.shape[2], frames.shape[1])

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "fatal",
        "-framerate",
        str(fps),
        "-f",
        "rawvideo",
        "-s",
        frame_size,
        "-pix_fmt",
        pixel_format,
        "-i",
        "-",
        "-an",
        "-crf",
        str(crf),
        "-vcodec",
        codec,
        "-preset",
        "ultrafast",
        "-threads",
        str(threads),
        "-slices",
        str(slices),
        "-slicecrc",
        str(slicecrc),
        "-r",
        str(fps),
        filename,
    ]

    if get_cmd:
        return command

    if not pipe:
        pipe = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for i in range(frames.shape[0]):
        pipe.stdin.write(frames[i, :, :].tobytes())

    if close_pipe:
        pipe.stdin.close()
        return None
    else:
        return pipe


def write_images(image_queue, filename_prefix, save_ir=True):
    """
    start writing the images to videos

    Args:
        image_queue (Subprocess.queues.Queue): data stream from the camera
        filename_prefix (str): base directory where the videos are saved
        save_ir (bool, optional): boolean flag to save ir video. Defaults to True.
    """
    depth_pipe = None
    if save_ir:
        ir_pipe = None

    while True:
        data = image_queue.get()
        if len(data) == 0:
            depth_pipe.stdin.close()
            if save_ir:
                ir_pipe.stdin.close()
            break
        else:
            ir, depth = data
            depth_pipe = write_frames(
                os.path.join(filename_prefix, "depth.avi"),
                depth[None, :, :],
                codec="ffv1",
                close_pipe=False,
                pipe=depth_pipe,
                pixel_format="gray16",
            )
            if save_ir:
                ir_pipe = write_frames(
                    os.path.join(filename_prefix, "ir.avi"),
                    ir[None, :, :],
                    close_pipe=False,
                    codec="ffv1",
                    pipe=ir_pipe,
                    pixel_format="gray16",
                )


# add camera related stuff here
def write_metadata(
    filename_prefix,
    subject_name,
    session_name,
    depth_resolution=[640, 576],
    little_endian=True,
    color_resolution=[640, 576],
):
    """
    write recording metadata as json file.

    Args:
        filename_prefix (str): session directory to save recording metadata file in
        subject_name (str): subject name of the recording
        session_name (str): session name of the recording
        depth_resolution (list, optional): frame resolution of depth videos. Defaults to [640, 576].
        little_endian (bool, optional): boolean flag that indicates if depth data is little endian. Defaults to True.
        color_resolution (list, optional): frame resolution of ir video. Defaults to [640, 576].
    """

    # construct metadata dictionary
    metadata_dict = {
        "SubjectName": subject_name,
        "SessionName": session_name,
        "DepthResolution": depth_resolution,
        "IsLittleEndian": little_endian,
        "ColorResolution": color_resolution,
        "StartTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }

    metadata_name = os.path.join(filename_prefix, "metadata.json")

    with open(metadata_name, "w") as output:
        json.dump(metadata_dict, output, indent=2)


def write_frames_pyav(filename, frames, fps=30, crf=10, pixel_format='gray', codec='libx264'):
    """
    Write frames using PyAV.

    Args:

    filename (str): File to write video to
    frames (numpy.array): NumPy array representing the frame data
    fps (int): Video fps
    crf (int): Constant rate factor that controls the quality of video encoding (lower CRF = higher quality)
    pixel_format (str): Parameter representing how the images are processed
    codec (str): Video codec to be encoded in
    """
    container = av.open(filename, mode='w')
    stream = container.add_stream(codec, rate=fps)
    stream.width = frames.shape[2]
    stream.height = frames.shape[1]
    stream.pix_fmt = pixel_format
    stream.options = {'crf': str(crf)}

    for frame in frames:
        av_frame = av.VideoFrame.from_ndarray(frame, format=pixel_format)
        packet = stream.encode(av_frame)
        container.mux(packet)

    # Flush the stream
    packet = stream.encode()
    while packet:
        container.mux(packet)
        packet = stream.encode()

    container.close()

def write_images_pyav(image_queue, filename_prefix, save_ir=True):
    """
    Write images with PyAV

    Args:

    image_queue (multiprocessing.queues.Queue): The data stream from the camera
    filename_prefix (str): Where the images will be written
    save_ir (bool): Whether to write IR images or not
    """
    depth_container = av.open(f"{filename_prefix}/depth.avi", mode='w')
    depth_stream = depth_container.add_stream('ffv1', rate=30)
    depth_stream.pix_fmt = 'gray16le'
    depth_stream.options = {'crf': '10'}

    if save_ir:
        ir_container = av.open(f"{filename_prefix}/ir.avi", mode='w')
        ir_stream = ir_container.add_stream('ffv1', rate=30)
        ir_stream.pix_fmt = 'gray16le'
        ir_stream.options = {'crf': '10'}

    while True:
        data = image_queue.get()
        if len(data) == 0:
            break
        else:
            ir, depth = data
            depth_frame = av.VideoFrame.from_ndarray(depth, format='gray16le')
            depth_packet = depth_stream.encode(depth_frame)
            depth_container.mux(depth_packet)

            if save_ir:
                ir_frame = av.VideoFrame.from_ndarray(ir, format='gray16le')
                ir_packet = ir_stream.encode(ir_frame)
                ir_container.mux(ir_packet)

    # Flush the streams
    for packet in depth_stream.encode():
        depth_container.mux(packet)
    depth_container.close()

    if save_ir:
        for packet in ir_stream.encode():
            ir_container.mux(packet)
        ir_container.close()

def start_recording(
    base_dir,
    subject_name,
    session_name,
    recording_length,
    save_ir=True,
    display_frames=True,
    display_time=True,
    depth_height_threshold=150,
):
    """
    start recording data.

    Args:
        base_dir (str): project base directory to save all videos
        subject_name (str): subject name of the recording
        session_name (str): session name of the recording
        recording_length (int): recording time in seconds.
        device_id (int, optional): camera id number if there are multiple cameras. Defaults to 0.
    """

    PRINT_INTERVAL = 30  # print every 30 frames

    filename_prefix = os.path.join(
        base_dir, subject_name + "_" + session_name + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
    )
    filename_prefix = os.path.expanduser(filename_prefix)
    os.makedirs(filename_prefix, exist_ok=True)

    # write recording metadata
    write_metadata(filename_prefix, subject_name, session_name)

    # start image writing process
    image_queue = Queue()
    write_process = Process(
        target=write_images,
        args=(image_queue, filename_prefix),
        kwargs={"save_ir": save_ir},
    )
    #write_process = Process(
       # target=write_images_pyav,
       # args=(image_queue, filename_prefix),
       # kwargs={"save_ir": save_ir},
   # )
    write_process.start()

    if display_frames:
        display_queue = Queue()
        display_process = Process(
            target=display_images, args=(display_queue, depth_height_threshold)
        )
        display_process.start()

    # define the camera
    pipeline = Pipeline()
    config = Config()
    # set up depth stream
    profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
    depth_profile = profile_list.get_video_stream_profile(640, 0, OBFormat.Y16, 30)
    if depth_profile is None:
        raise ValueError(
            "Depth stream unable to initialize. Make sure there is a USB connection to the camera."
        )
    config.enable_stream(depth_profile)

    # set up ir stream
    profile_list = pipeline.get_stream_profile_list(OBSensorType.IR_SENSOR)
    ir_profile = profile_list.get_video_stream_profile(640, 0, OBFormat.Y16, 30) # important: SET THE FPS
    config.enable_stream(ir_profile)

    # start the camera
    pipeline.start(config)

    # set up timestamp recording
    system_timestamps = []
    device_timestamps = []
    start_time = time.time()
    print("Start time:", datetime.fromtimestamp(start_time))
    count = 0

    # the actual recording
    try:
        while time.time() - start_time < recording_length:
            frames = pipeline.wait_for_frames(200)
            if frames is None:
                print("Dropped frame")
                continue

            # record system timestamp
            system_timestamps.append(time.time())

            depth_frame = frames.get_depth_frame()
            if depth_frame is None:
                continue

            # record device timestamp
            device_timestamps.append(depth_frame.get_timestamp())
            width = depth_frame.get_width()
            height = depth_frame.get_height()
            scale = depth_frame.get_depth_scale()

            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            depth_data = depth_data.reshape((height, width))
            depth_data = (depth_data * scale).astype(np.uint16)

            # get ir frames
            ir_frame = frames.get_ir_frame()
            if ir_frame is None:
                continue

            ir_data = np.asanyarray(ir_frame.get_data())
            width = ir_frame.get_width()
            height = ir_frame.get_height()
            ir_data = np.frombuffer(ir_data, dtype=np.uint16)
            ir_data = np.resize(ir_data, (height, width))

            image_queue.put((ir_data, depth_data))
            if display_frames and count % 2 == 0:
                display_queue.put((ir_data, depth_data))
            
            fps_0 = None

            if display_time and count > 0 and (count % PRINT_INTERVAL) == 0:
                fps = len(system_timestamps) / (
                    max(system_timestamps) - min(system_timestamps)
                )

                if count == 1:
                    fps_0 = fps
                    if fps_0 is not None:
                        print(f" - The initial frame rate is {fps_0:0.2f}", end="")
                print(
                    f"\rRecorded {int(time.time() - start_time):02d} of {recording_length} seconds",
                    end="",
                )
                print(f" - Current frame rate {fps:0.2f} fps", end="")
                if fps < 29.5:
                    print("WARNING: LOW FRAME RATE")
                elif fps_0 is not None and fps < fps_0 * 0.9:
                    print("WARNING: FRAME RATE FLUCTUATION")
            count += 1
    except OSError:
        print("Recording stopped early")

    finally:
        pipeline.stop()
        device_timestamps = np.array(device_timestamps)

        np.savetxt(
            os.path.join(filename_prefix, "depth_ts.txt"), device_timestamps, fmt="%f"
        )
        np.savetxt(
            os.path.join(filename_prefix, "system_ts.txt"),
            np.array(system_timestamps),
            fmt="%f",
        )

        fps = len(system_timestamps) / (max(system_timestamps) - min(system_timestamps))
        print(f" - Session average frame rate = {fps:0.2f} fps")
        messagebox.showinfo("Recording completed!", f"The recordings and information has been saved at {filename_prefix}")
        image_queue.put(tuple())
        write_process.join()

        if display_frames:
            display_queue.put(tuple())
            display_process.join()
