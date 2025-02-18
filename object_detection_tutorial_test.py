
# coding: utf-8

# # Object Detection Demo
# Welcome to the object detection inference walkthrough!  This notebook will walk you step by step through the process of using a pre-trained model to detect objects in an image. Make sure to follow the [installation instructions](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md) before you start.

# # Imports

# In[1]:


import numpy as np
import os
import sys
import tensorflow as tf
import time

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("./object_detection")
from object_detection.utils import ops as utils_ops

if tf.__version__ < '1.4.0':
  raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')


# ## Env setup

# In[ ]:




# ## Object detection imports
# Here are the imports from the object detection module.

# In[ ]:


from utils import label_map_util


# # Model preparation

# ## Variables
#
# Any model exported using the `export_inference_graph.py` tool can be loaded here simply by changing `PATH_TO_CKPT` to point to a new .pb file.
#
# By default we use an "SSD with Mobilenet" model here. See the [detection model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) for a list of other models that can be run out-of-the-box with varying speeds and accuracies.

# In[ ]:


# What model to download.
MODEL_NAME = 'classification_model'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('classification_model', 'label_map.pbtxt')

NUM_CLASSES = 4


# ## Download Model

# ## Load a (frozen) Tensorflow model into memory.

# In[ ]:

def getDetectionGraph():
    detection_graph = tf.Graph()
    with detection_graph.as_default():
      od_graph_def = tf.GraphDef()
      with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')
    return detection_graph


# ## Loading label map
# Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine

# In[ ]:

def getLabelMapCategories():
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map,
        max_num_classes=NUM_CLASSES, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)
    return category_index



# ## Helper code

# In[ ]:


def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)



# In[ ]:

category_index = getLabelMapCategories()
detection_graph = getDetectionGraph()
#inp = input("Input your image path: ")
inp = './object_detection/real_images/image4.jpg'
image = Image.open(str(inp))
# the array based representation of the image will be used later in order to prepare the
# result image with boxes and labels on it.
image_np = load_image_into_numpy_array(image)
image_np = np.expand_dims(image_np, 0)
#image_np = tf.gfile.FastGFile(inp, 'rb').read()
# Expand dimensions since the model expects images to have shape: [1, None, None, 3]
# Actual detection.
with detection_graph.as_default():
    with tf.Session() as sess:
        # Get handles to input and output tensors
        ops = tf.get_default_graph().get_operations()
        all_tensor_names = {output.name for op in ops for output in op.outputs}
        tensor_dict = {}
        for key in ['detection_scores', 'detection_classes']:
            tensor_name = key + ':0'
            if tensor_name in all_tensor_names:
                tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                    tensor_name)
        image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')
        # Run inference
        start = time.time()
        output_dict = sess.run(tensor_dict, feed_dict={image_tensor: image_np})
        end = time.time()
        print (end - start)
        # all outputs are float32 numpy arrays, so convert types as appropriate
        output_dict['detection_classes'] = output_dict['detection_classes'][0].astype(np.uint8)
        #output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
        output_dict['detection_scores'] = output_dict['detection_scores'][0]
# Visualization of the results of a detection.
max_detect = np.argmax(output_dict['detection_scores'])
if (output_dict['detection_scores'][max_detect] > 0.5):
    max_class = (output_dict['detection_classes'])[max_detect]
    print (category_index[max_class]['name'])
else:
    print (0)
