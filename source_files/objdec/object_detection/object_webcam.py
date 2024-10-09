#!/usr/bin/env python
# coding: utf-8

# # Object Detection API Demo
# 
# <table align="left"><td>
#   <a target="_blank"  href="https://colab.sandbox.google.com/github/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb">
#     <img src="https://www.tensorflow.org/images/colab_logo_32px.png" />Run in Google Colab
#   </a>
# </td><td>
#   <a target="_blank"  href="https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb">
#     <img width=32px src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" />View source on GitHub</a>
# </td></table>''

# Welcome to the [Object Detection API](https://github.com/tensorflow/models/tree/master/research/object_detection). This notebook will walk you step by step through the process of using a pre-trained model to detect objects in an image.

# > **Important**: This tutorial is to help you through the first step towards using [Object Detection API](https://github.com/tensorflow/models/tree/master/research/object_detection) to build models. If you just just need an off the shelf model that does the job, see the [TFHub object detection example](https://colab.sandbox.google.com/github/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb).

# # Setup

# Important: If you're running on a local machine, be sure to follow the [installation instructions](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md). This notebook includes only what's necessary to run in Colab.

# ### Install

# In[ ]:


get_ipython().magic('matplotlib inline')
sys.path.append("..")


# Make sure you have `pycocotools` installed

# In[ ]:


#get_ipython().system('pip install pycocotools')


# Get `tensorflow/models` or `cd` to parent directory of the repository.

# In[ ]:


##import os
##import pathlib


#if "models" in pathlib.Path.cwd().parts:
# while "models" in pathlib.Path.cwd().parts:
#    os.chdir('..')
#elif not pathlib.Path('models').exists():
#  get_ipython().system('git clone --depth 1 https://github.com/tensorflow/models')


# Compile protobufs and install the object_detection package

# In[ ]:


get_ipython().run_cell_magic('bash', '', 'cd models/research/\nprotoc object_detection/protos/*.proto --python_out=.')


# In[ ]:


get_ipython().run_cell_magic('bash', '', 'cd models/research\npip install .')


# ### Imports

# In[ ]:


import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
#from IPython.display import display


# Import the object detection module.

# In[ ]:


from utils import label_map_util
from utils import visualization_utils as vis_util


# Patches:

# In[ ]:


# patch tf1 into `utils.ops`
utils_ops.tf = tf.compat.v1

# Patch the location of gfile
tf.gfile = tf.io.gfile


# # Model preparation 

# ## Variables
# 
# Any model exported using the `export_inference_graph.py` tool can be loaded here simply by changing the path.
# 
# By default we use an "SSD with Mobilenet" model here. See the [detection model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) for a list of other models that can be run out-of-the-box with varying speeds and accuracies.

# ## Loader

# In[ ]:


#def load_model(model_name):
#  base_url = 'http://download.tensorflow.org/models/object_detection/'
#  model_file = model_name + '.tar.gz'
#  model_dir = tf.keras.utils.get_file(
#    fname=model_name, 
#    origin=base_url + model_file,
#    untar=True)#
#
#  model_dir = pathlib.Path(model_dir)/"saved_model"

  #model = tf.saved_model.load(str(model_dir))
 # model = model.signatures['serving_default']

  #return model


# ## Loading label map
# Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine

# In[ ]:


# List of the strings that is used to add correct label for each box.
#PATH_TO_LABELS = 'models/research/object_detection/data/mscoco_label_map.pbtxt'
#category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)


# For the sake of simplicity we will test on 2 images:

# In[ ]:


# If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
#PATH_TO_TEST_IMAGES_DIR = pathlib.Path('models/research/object_detection/test_images')
#TEST_IMAGE_PATHS = sorted(list(PATH_TO_TEST_IMAGES_DIR.glob("*.jpg")))
#TEST_IMAGE_PATHS


# # Detection

# Load an object detection model:

# In[ ]:


MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE= 'http://download.tensorflow.org/models/object_detection/'
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
PATH_TO_LABELS = os.path.join('data','mscoco_label_map.pbtxt')
NUM_CLASSES = 90
#detection_model = load_model(model_name)


# Check the model's input signature, it expects a batch of 3-color images of type uint8: 

# In[ ]:

#print(detection_model.inputs)
opener = urllib.request.URLopener()
opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
tar_file = tarfile.open(MODEL_FILE)
for file in tar_file.getmembers():
    file_name = os.path.basename(file.name)
    if 'frozen_inference_graph.pb' in file_name:
        tar_file.extract(file,os.getcwd())

# And retuns several outputs:

# In[ ]:

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialzed_graph = fid.read()
        od_graph_def.ParseFromString(serialzed_graph)
        tf.import_graph_def(od_graph_def, name= '')
#detection_model.output_dtypes


# In[ ]:
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map,
                                    max_num_classes=NUM_CLASSES,
                                    use_display_name=True)
category_index = label_map_util.create_category_index(categories)

#detection_model.output_shapes


# Add a wrapper function to call the model, and cleanup the outputs:

# In[ ]:

def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

# =============================================================================
# def run_inference_for_single_image(model, image):
#   image = np.asarray(image)
#   # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
#   input_tensor = tf.convert_to_tensor(image)
#   # The model expects a batch of images, so add an axis with `tf.newaxis`.
#   input_tensor = input_tensor[tf.newaxis,...]
# 
#   # Run inference
#   output_dict = model(input_tensor)
# 
#   # All outputs are batches tensors.
#   # Convert to numpy arrays, and take index [0] to remove the batch dimension.
#   # We're only interested in the first num_detections.
#   num_detections = int(output_dict.pop('num_detections'))
#   output_dict = {key:value[0, :num_detections].numpy() 
#                  for key,value in output_dict.items()}
#   output_dict['num_detections'] = num_detections
# 
#   # detection_classes should be ints.
#   output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
#    
#   # Handle models with masks:
#   if 'detection_masks' in output_dict:
#     # Reframe the the bbox mask to the image size.
#     detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
#               output_dict['detection_masks'], output_dict['detection_boxes'],
#                image.shape[0], image.shape[1])      
#     detection_masks_reframed = tf.cast(detection_masks_reframed > 0.5,
#                                        tf.uint8)
#     output_dict['detection_masks_reframed'] = detection_masks_reframed.numpy()
#     
#   return output_dict
# 
# =============================================================================

# Run it on each test image and show the results:

# In[ ]:
PATH_TO_TEST_IMAGES_DIR = 'test_images'
TEST_IMAGE_PATHS = [ os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i))for i in range(1,3)]
IMAGE_SIZE = (12, 8)

# =============================================================================
# def show_inference(model, image_path):
#   # the array based representation of the image will be used later in order to prepare the
#   # result image with boxes and labels on it.
#   image_np = np.array(Image.open(image_path))
#   # Actual detection.
#   output_dict = run_inference_for_single_image(model, image_np)
#   # Visualization of the results of a detection.
#   vis_util.visualize_boxes_and_labels_on_image_array(
#       image_np,
#       output_dict['detection_boxes'],
#       output_dict['detection_classes'],
#       output_dict['detection_scores'],
#       category_index,
#       instance_masks=output_dict.get('detection_masks_reframed', None),
#       use_normalized_coordinates=True,
#       line_thickness=8)
# 
#   display(Image.fromarray(image_np))
# =============================================================================


# In[ ]:
import cv2
cap=cv2.VideoCapture(0)
with detection_graph.as_default():
        with tf.compat.v1.Session(graph=detection_graph) as sess:
            ret = True
            while (ret):
         #   for image_path in TEST_IMAGE_PATHS:
                   # image = Image.open(image_path)
                   # image_np = load_image_into_numpy_array(image) 
                    ret,image_np = cap.read()
                    image_np_expanded = np.expand_dims(image_np, axis=0)
                    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
                    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
                    scores = detection_graph.get_tensor_by_name('detection_scores:0')
                    classes = detection_graph.get_tensor_by_name('detection_classes:0')
                    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
                    
                    (boxes, scores, classes, num_detections) = sess.run([boxes, scores, classes, num_detections],
                    feed_dict = {image_tensor: image_np_expanded})
                    
                    vis_util.visualize_boxes_and_labels_on_image_array(
                            image_np,
                            np.squeeze(boxes),
                            np.squeeze(classes).astype(np.int32),
                            np.squeeze(scores),
                            category_index,
                            use_normalized_coordinates=True,
                            line_thickness = 8)
                    cv2.imshow('image',cv2.resize(image_np,(1280,960)))
                    if cv2.waitKey(25) & 0xFF == ord('q'):
                        break
                        cv2.destroyAllWindows()
                        cap.release()
# =============================================================================
#                     plt.figure(figsize=IMAGE_SIZE)
#                     plt.imshow(image_np)
# 
# =============================================================================
# =============================================================================
# for image_path in TEST_IMAGE_PATHS:
#   show_inference(detection_model, image_path)
# =============================================================================


# ## Instance Segmentation

# In[ ]:


model_name = "mask_rcnn_inception_resnet_v2_atrous_coco_2018_01_28"
masking_model = load_model("mask_rcnn_inception_resnet_v2_atrous_coco_2018_01_28")


# The instance segmentation model includes a `detection_masks` output:

# In[ ]:


masking_model.output_shapes


# In[ ]:


for image_path in TEST_IMAGE_PATHS:
  show_inference(masking_model, image_path)


# In[ ]:




# -*- coding: utf-8 -*-

