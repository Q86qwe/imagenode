"""FPS_receive_jpg_test.py -- receive jpg compressed images & print FPS stats

A test program to provide FPS statistics as different imagenode algorithms are
being tested. This program receives images that have been jpg compressed and
computes and prints FPS statistics. It requires a FPS_test.yaml file with
appropriate options in the home directory of the receiving computer. There is a
similar program that receives images rather than jpg compressed images.

1. Edit the FPS_test.yaml file and copy it to the home directory of the
   receiving Mac.

2. Set the yaml options on the imagenode sending RPi in the imagenode.yaml
   file at the home directory.

2. Run this program in its own terminal window on the mac:
   python FPS_receive_jpg_test.py.

   This 'receive images' program must be running before starting
   the RPi image sending program.

2. Run the imagenode image sending program on the RPi:
   python imagenode.py

A cv2.imshow() window will only appear on the Mac that is receiving the
tramsmitted images if the "show_images" option in the yaml file is set to True.
The receiving program will run until the "number_of_images" option in the yaml
file is reached or until Ctrl-C is pressed.

The imagenode program running on the RPi will end itself after a timeout or you
can end it by pressing Ctrl-C.

For details see the docs/FPS-tests.rst file.
"""

import sys

import time
import traceback
import numpy as np
import cv2
from collections import defaultdict
from imutils.video import FPS
import imagezmq

# instantiate image_hub
image_hub = imagezmq.ImageHub()

image_count = 0
sender_image_counts = defaultdict(int)  # dict for counts by sender
first_image = True

try:
    while True:  # receive images until Ctrl-C is pressed
        sent_from, jpg_buffer = image_hub.recv_jpg()
        if first_image:
            fps = FPS().start()  # start FPS timer after first image is received
            first_image = False
        image = cv2.imdecode(np.frombuffer(jpg_buffer, dtype='uint8'), -1)
        # see opencv docs for info on -1 parameter
        fps.update()
        image_count += 1  # global count of all images received
        sender_image_counts[sent_from] += 1  # count images for each RPi name
        cv2.imshow(sent_from, image)  # display images 1 window per sent_from
        cv2.waitKey(1)
        # other image processing code, such as saving the image, would go here.
        # often the text in "sent_from" will have additional information about
        # the image that will be used in processing the image.
        image_hub.send_reply(b'OK')  # REP reply
except (KeyboardInterrupt, SystemExit):
    pass  # Ctrl-C was pressed to end program; FPS stats computed below
except Exception as ex:
    print('Python error with no Exception handler:')
    print('Traceback error:', ex)
    traceback.print_exc()
finally:
    # stop the timer and display FPS information
    print()
    print('Test Program: ', __file__)
    print('Total Number of Images received: {:,g}'.format(image_count))
    if first_image:  # never got images from any RPi
        sys.exit()
    fps.stop()
    print('Number of Images received from each RPi:')
    for RPi in sender_image_counts:
        print('    ', RPi, ': {:,g}'.format(sender_image_counts[RPi]))
    compressed_size = len(jpg_buffer)
    print('Size of last jpg buffer received: {:,g} bytes'.format(compressed_size))
    image_size = image.shape
    print('Size of last image received: ', image_size)
    uncompressed_size = 1
    for dimension in image_size:
        uncompressed_size *= dimension
    print('    = {:,g} bytes'.format(uncompressed_size))
    print('Compression ratio: {:.2f}'.format(compressed_size / uncompressed_size))
    print('Elasped time: {:,.2f} seconds'.format(fps.elapsed()))
    print('Approximate FPS: {:.2f}'.format(fps.fps()))
    cv2.destroyAllWindows()  # closes the windows opened by cv2.imshow()
    image_hub.close()  # closes ZMQ socket and context
    sys.exit()
