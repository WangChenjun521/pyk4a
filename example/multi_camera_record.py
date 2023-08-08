from argparse import ArgumentParser

from pyk4a import Config, ImageFormat, PyK4A, PyK4ARecord,FPS,DepthMode

import os
# import asyncio
import time

def main(args):

    print(f"Starting device0 #{args.device0}")
    print(f"Starting device1 #{args.device1}")
    
    config0=Config(camera_fps=FPS.FPS_30,depth_mode=DepthMode.NFOV_UNBINNED,depth_delay_off_color_usec=-80)
    config1=Config(camera_fps=FPS.FPS_30,depth_mode=DepthMode.NFOV_UNBINNED,depth_delay_off_color_usec=80)
    # config=Config(camera_fps=FPS.FPS_30,subordinate_delay_off_master_usec=1)
    ## device0
    device0 = PyK4A(config=config0, device_id=args.device0)
    device1 = PyK4A(config=config1, device_id=args.device1)
    device0.start()
    device1.start()
    # path0=os.path.join(args.FILE,"_0.mkv")
    path0=args.FILE+"_0.mkv"
    print(f"Open record file {path0}")
    record0 = PyK4ARecord(device=device0, config=config0, path=path0)
    


    ## device1
    
    
    # path1=os.path.join(args.FILE,"_1.mkv")
    path1=args.FILE+"_1.mkv"
    print(f"Open record file {path1}")
    record1 = PyK4ARecord(device=device1, config=config1, path=path1)
    record0.create()
    record1.create()

    try:
        # loop = asyncio.get_event_loop()
        print("Recording... Press CTRL-C to stop recording.")
        while True:
            capture0 = device0.get_capture()
            capture1 = device1.get_capture()
            record0.write_capture(capture0)
            record1.write_capture(capture1)
            # tasks = asyncio.gather(device0.get_capture(), device1.get_capture())
            # results = loop.run_until_complete(tasks)    
    except KeyboardInterrupt:
        print("CTRL-C pressed. Exiting.")

    record0.flush()
    record0.close()
    print(f"{record0.captures_count} frames written.")

    record1.flush()
    record1.close()
    print(f"{record1.captures_count} frames written.")


if __name__ == "__main__":
    parser = ArgumentParser(description="pyk4a recorder")
    parser.add_argument("--device0", type=int, help="Device ID", default=0)
    parser.add_argument("--device1", type=int, help="Device ID", default=1)
    parser.add_argument("--FILE", type=str, help="Path to MKV file",default="C:/data/new_data_mkv/seq0099")
    args = parser.parse_args()
    main(args)
