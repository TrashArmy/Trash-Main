import tensorflow as tf, sys

image_path = './object_detection/real_images/image10.jpg'
graph_path = './classification_model/frozen_inference_graph.pb'
labels_path = './classification_model/output_labels.txt'

# Read in the image_data
image_data = tf.gfile.FastGFile(image_path, 'rb').read()

# Loads label file, strips off carriage return
label_lines = {
  1: 'aluminum_can',
  2: 'plastic_cup',
  3: 'plastic_bottle',
  4: 'paper_cup'
}


# Unpersists graph from file
with tf.gfile.FastGFile(graph_path, 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    _ = tf.import_graph_def(graph_def, name='')

# Feed the image_data as input to the graph and get first prediction
with tf.Session() as sess:
    softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
    predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
    # Sort to show labels of first prediction in order of confidence
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
    print (top_k)
