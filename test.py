
import time

import numpy as np
import tensorflow as tf

ACTUAL_LABELS_FOR_TEST = [
    "paper cup", "paper cup", "paper cup", "paper cup", "paper cup", "paper cup", "paper cup", "paper cup",
    "plastic bottle", "plastic bottle", "plastic bottle", "plastic bottle", "plastic bottle", "plastic bottle",
    "plastic bottle", "plastic bottle", "plastic bottle", "plastic bottle", "aluminum can", "aluminum can",
    "aluminum can", "aluminum can", "aluminum can", "aluminum can", "aluminum can", "aluminum can", "aluminum can",
    "aluminum can", "aluminum can", "aluminum can", "aluminum can", "aluminum can", "aluminum can", "plastic cup",
    "plastic cup", "plastic cup", "plastic cup", "plastic cup", "plastic cup", "plastic cup", "plastic cup", "plastic cup",
    "plastic cup", "paper cup holder", "paper cup holder", "paper cup holder", "plastic cup lid", "plastic cup lid", "plastic cup lid",
    "non recyclables", "non recyclables"
]

def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()
    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
        with graph.as_default():
            tf.import_graph_def(graph_def)
    return graph

def read_tensor_from_image_file(file_name, input_height=299, input_width=299, input_mean=0, input_std=255):
    input_name = "file_reader"
    output_name = "normalized"
    file_reader = tf.read_file(file_name, input_name)
    if file_name.endswith(".png"):
        image_reader = tf.image.decode_png(file_reader, channels = 3, name='png_reader')
    elif file_name.endswith(".gif"):
        image_reader = tf.squeeze(tf.image.decode_gif(file_reader, name='gif_reader'))
    elif file_name.endswith(".bmp"):
        image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
    else:
        image_reader = tf.image.decode_jpeg(file_reader, channels = 3, name='jpeg_reader')
    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0);
    resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)
    return result


def load_labels(label_file):
    label = []
    proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
    for l in proto_as_ascii_lines:
        label.append(l.rstrip())
    return label

def get_classified_result():
    image_name_base = './test_images/'
    path_to_model = './mobilenet_model/retrained_graph.pb'
    path_to_labels = './mobilenet_model/retrained_labels.txt'
    input_height = 224
    input_width = 224
    input_mean = 128
    input_std = 128
    input_layer = "input"
    output_layer = "final_result"
    graph = load_graph(path_to_model)
    labels = load_labels(path_to_labels)
    CLASSIFICATION_DICT = {"aluminum can": 3, "plastic cup": 2, "plastic bottle": 2,
                            "paper cup": 0}
    uu = 0
    start = time.time()
    for i in range(1, 52):
        try :
            file_name = image_name_base + str(i) + '.jpg'
            image_tensor = read_tensor_from_image_file(file_name, input_height=input_height, input_width=input_width, input_mean=input_mean, input_std=input_std)
        except:
            continue
        input_name = "import/" + input_layer
        output_name = "import/" + output_layer
        input_operation = graph.get_operation_by_name(input_name);
        output_operation = graph.get_operation_by_name(output_name);
        with tf.Session(graph=graph) as sess:
            start = time.time()
            results = sess.run(output_operation.outputs[0], {input_operation.outputs[0]: image_tensor})
            end=time.time()
        results = np.squeeze(results)
        top_k = results.argsort()[-5:][::-1]
        top_k = top_k[0]
        #print ((labels[top_k]), ACTUAL_LABELS_FOR_TEST[i- 1])
        #print ((labels[top_k])==ACTUAL_LABELS_FOR_TEST[i - 1])
        if (labels[top_k]==ACTUAL_LABELS_FOR_TEST[i - 1]):
            uu += 1
        else:
            print (file_name)
            print (ACTUAL_LABELS_FOR_TEST[i - 1])
    end = time.time()
    print (uu)
    print (uu * 100/51)
    print (end - start)

get_classified_result()
