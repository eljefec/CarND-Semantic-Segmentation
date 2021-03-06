import os.path
import tensorflow as tf
import helper
import time
import warnings
from distutils.version import LooseVersion
import project_tests as tests


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    # Load the model and weights.
    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)

    graph = sess.graph

    return (graph.get_tensor_by_name(vgg_input_tensor_name),
            graph.get_tensor_by_name(vgg_keep_prob_tensor_name),
            graph.get_tensor_by_name(vgg_layer3_out_tensor_name),
            graph.get_tensor_by_name(vgg_layer4_out_tensor_name),
            graph.get_tensor_by_name(vgg_layer7_out_tensor_name))

tests.test_load_vgg(load_vgg, tf)


def conv2d(input, filters, kernel_size, strides):
    # l2_regularizer and truncated_normal_initializer are recommended by https://discussions.udacity.com/t/why-my-inference-images-have-green-dot-labeled-all-over-the-image/368946/5
    return tf.layers.conv2d(input, filters, kernel_size, strides, padding='same',
                            kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                            kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))

def conv2d_transpose(input, filters, kernel_size, strides):
    return tf.layers.conv2d_transpose(input, filters, kernel_size, strides, padding='same',
                                      kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                      kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))

def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # Layers are based on https://github.com/developmentseed/caffe-fcn/blob/master/fcn-8s/train_val.prototxt
    score = conv2d(vgg_layer7_out, num_classes, 1, 1)

    upscore2 = conv2d_transpose(score, num_classes, 4, 2)
    score_pool4 = conv2d(vgg_layer4_out, num_classes, 1, 1)

    score_fused = tf.add(upscore2, score_pool4)

    score4 = conv2d_transpose(score_fused, num_classes, 4, 2)
    score_pool3 = conv2d(vgg_layer3_out, num_classes, 1, 1)

    score_final = tf.add(score4, score_pool3)
    bigscore = conv2d_transpose(score_final, num_classes, 16, 8)

    return bigscore

tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    labels = tf.reshape(correct_label, (-1, num_classes))

    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=logits)
    cross_entropy_loss = tf.reduce_mean(cross_entropy)

    optimizer = tf.train.AdamOptimizer(learning_rate = learning_rate)
    train_op = optimizer.minimize(cross_entropy_loss)

    return logits, train_op, cross_entropy_loss

tests.test_optimize(optimize)


def get_epoch(checkpoint_file):
    filename = os.path.basename(checkpoint_file)
    parts = filename.split('.')[0].split('-')
    return int(parts[-1])


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate, checkpoint_dir = None):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    sess.run(tf.global_variables_initializer())

    start_epoch = 0

    if checkpoint_dir:
        saver = tf.train.Saver(max_to_keep = 10)
        if os.path.exists(checkpoint_dir):
            latest = tf.train.latest_checkpoint(checkpoint_dir)
            if latest:
                start_epoch = get_epoch(latest) + 1
                saver.restore(sess, latest)
                print('Restored latest checkpoint at epoch {}.'.format(start_epoch - 1))
        else:
            os.makedirs(checkpoint_dir)

    stop_epoch = start_epoch + epochs

    for i in range(start_epoch, stop_epoch):
        print('EPOCH {} of {}'.format(i+1, stop_epoch))
        for images, labels in get_batches_fn(batch_size):
            _, loss = sess.run([train_op, cross_entropy_loss],
                               feed_dict = {input_image: images,
                                            correct_label: labels,
                                            keep_prob: 0.2,
                                            learning_rate: 0.001})
        print('EPOCH {}, loss = {}'.format(i+1, loss))

        if checkpoint_dir:
            saver.save(sess, os.path.join(checkpoint_dir, 'checkpoint'), global_step = i)
            print('Saved checkpoint at epoch {}'.format(i))

tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    checkpoint_dir = './checkpoints'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        input_image, keep_prob, vgg_layer3_out, vgg_layer4_out, vgg_layer7_out = load_vgg(sess, vgg_path)
        score_final = layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes)
        correct_label = tf.placeholder(tf.float32, [None, None, None, num_classes])
        learning_rate = tf.placeholder(tf.float32)
        logits, train_op, cross_entropy_loss = optimize(score_final, correct_label, learning_rate, num_classes)

        epochs = 16
        batch_size = 1

        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image, correct_label, keep_prob, learning_rate, checkpoint_dir)

        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
