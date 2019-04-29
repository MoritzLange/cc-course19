"""Group GPRI's main file.

Contains initialize- and create-functions.
"""

import os
import contextlib
import sys
import csv
import time
import cv2
import numpy as np
import numpy.random as npr
import tensorflow as tf
import tensorflow_hub as hub
import logging
import shutil
import imageio
from google_images_download import google_images_download
from .gpri_helper import style_image_funcs

# silence tensorflow spurious-warnings
tf.logging.set_verbosity(tf.logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.disable(logging.WARNING)
logging.getLogger('tensorflow').disabled = True

# silence keras messages
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
sys.stderr = stderr

animal_idxs = np.arange(398)
activity_idxs = np.arange(398, 1000)


class RandomImageCreator:

    def __init__(self, *args, **kwargs):
        """Initialize any data structures, objects, etc. needed by the system so that the system is fully prepared
        when create-function is called.

        Only keyword arguments are supported in config.json
        """
        print("/----------------Group GPRI initialize----------------/")
        print("This code will need about 6GB or RAM while running (or about 4GB if you don't use the GAN)!\n")

        # Each creator should have domain specified: title, poetry, music, image, etc.
        self.domain = 'image'
        self.dims = kwargs.pop('resolution', [128, 128])
        self.folder = os.path.dirname(os.path.realpath(__file__))
        self.sess = None
        self.GAN_MODE = False

        # Create necessary folders
        os.makedirs(self.folder + '/images/output', exist_ok=True)
        os.makedirs(self.folder + '/images/style', exist_ok=True)
        os.makedirs(self.folder + '/images/content', exist_ok=True)


        # load style transfer gan_module
        global style_transfer
        from .gpri_helper import style_transfer

        # load inception gan_module for evaluation
        print("Loading Inception v3 network...")
        self.inception_module = hub.Module(
            'https://tfhub.dev/google/imagenet/inception_v3/classification/1')

        # Load the vectors for word -> vector based on glove model
        print("Loading GloVe vectors...")
        self.vec_list = self.load_glove_vecs()


        # Check if user wants to use BigGAN:
        choice = input("Enable GAN mode (y/n)? If no, initial image will "
                       "be fetched from Google instead of using BigGAN.")

        if choice == 'Y' or choice == 'y' or choice == 'yes':
            self.GAN_MODE = True
            print('GAN mode enabled.')
            print('Loading BigGAN model...')
            self.gan_module = hub.Module(
                'https://tfhub.dev/deepmind/biggan-deep-128/1')
        else:
            self.GAN_MODE = False
            print('GAN mode disabled. Will fetch a content image from '
                  'Google.')

    def generate(self, emotion, word_pairs, **kwargs):
        """Random image generator.
        """
        # Sample one of the word_pairs for use:
        wpr = word_pairs[npr.choice(len(word_pairs))]

        # Generate content image
        content_path = self.generate_contentImage(wpr)

        # generate style image
        style_path = self.generate_styleImage(emotion)

        # fetch another style image from Google
        google_style_path = self.get_googleImage([emotion] + list(wpr), True)

        cur_time = str(int(time.time() % 1e7))
        output_path = self.folder + "/images/output/" + cur_time + ".jpg"
        intermediate_output_path = self.folder + "/images/intermediate_output.jpg"

        style_transfer.stylize(alpha=0.1, content_path=content_path,
                               style_path=google_style_path,
                               output_path=intermediate_output_path)
        style_transfer.stylize(alpha=0.35, content_path=intermediate_output_path,
                               style_path=style_path, output_path=output_path)

        return output_path

    def generate_styleImage(self, emotion):
        """
        Generate the style image for the style transfer.
        :param emotion: Emotion input
        :return:
            String: Path of the style image.
        """
        cur_time = str(int(time.time() % 1e7))
        path = self.folder + "/images/style/" + cur_time + ".jpg"

        if emotion == "anger":
            print("Generating style image for anger ...")
            image = style_image_funcs.create_anger_image((128, 128), 180, 15, 5, 10)
            imageio.imwrite(path, image)

        elif emotion == "disgust":
            print("Generating style image for disgust ...")
            image = style_image_funcs.create_disgust_image((128, 128), 180, 10, 5, 3)
            imageio.imwrite(path, image)

        elif emotion == "fear":
            print("Generating style image for fear ...")
            image = style_image_funcs.create_fear_image((128, 128), 180, 15, 5, 10)
            imageio.imwrite(path, image)

        elif emotion == "happiness":
            print("Generating style image for happiness ...")
            image = style_image_funcs.create_happiness_image((128, 128), 180, 15, 5)
            imageio.imwrite(path, image)

        elif emotion == "sadness":
            print("Generating style image for sadness ...")
            image = style_image_funcs.create_sadness_image((128, 128), 180, 5)
            imageio.imwrite(path, image)

        elif emotion == "surprise":
            print("Generating style image for surprise ...")
            image = style_image_funcs.create_surprise_image((128, 128), 180, 15, 15, 25)
            imageio.imwrite(path, image)

        return path

    def get_googleImage(self, keywords, style):
        """
        Fetch the style image for the style transfer.
        :param keywords: List of words to search for
        :param style: Boolean, whether image should be abstract art, for the
            style image
        :return:
            Path to medium sized style or content image
        """
        print('Downloading an image from Google...')
        response = google_images_download.googleimagesdownload()
        search_term = ''
        for w in keywords:
            search_term = search_term + w + ' '
        if style:
            search_term = search_term + 'abstract art'

        arguments = {"keywords": search_term,
                     "limit": 1,
                     "size": "medium",
                     "format": "jpg",
                     "color_tye": "full-color",
                     "type": "photo",
                     "output_directory": f"{str(self.folder)}",
                     "image_directory": "images/google_style_dump"}

        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull):
                path = response.download(arguments)

        path = [k for k in path.values()]
        # rename the downloaded styleImage to a proper name
        img_path = ''
        try:
            cur_time = str(int(time.time() % 1e7))
            if style:
                img_path = self.folder + "/images/style/" + cur_time + ".jpg"
            else:
                img_path = self.folder + "/images/content/" + cur_time + ".jpg"
            shutil.move(str(path[0][0]), img_path)
        except:
            print('Image retrieved from Google could not be moved to correct '
                  'location!')
        return img_path

    def generate_contentImage(self, wpr):
        """
        Generates the intial image, the content image in terms of style
        transfer, from the 'noun' input variable. Currently only supports a
        sample image.
        :param wpr: A word pair
        :return:
            String with file path
        """

        # If GAN_MODE is disabled or the noun is 'human' or 'weather':
        if (not self.GAN_MODE) or (
                wpr[0] not in ['activity', 'animal', 'location']):
            path = self.get_googleImage(wpr, False)

        else:
            print("Generating image with GAN...")
            truncation = 0.5  # scalar truncation value in [0.0, 1.0]
            z = truncation * tf.random.truncated_normal(
                [1, 128])  # noise sample

            y_index = tf.Variable([self.sample_idx(wpr[0])], dtype=tf.int32)
            y = tf.one_hot(y_index, 1000)  # one-hot ImageNet label

            samples = self.gan_module(dict(y=y, z=z, truncation=truncation))

            initializer = tf.global_variables_initializer()
            with tf.Session() as sess:
                sess.run(initializer)
                img = sess.run(samples)[0]

            cur_time = str(int(time.time() % 1e7))
            path = self.folder + "/images/content/" + cur_time + ".jpg"
            imageio.imwrite(path, img)

        return path

    def sample_idx(self, noun):
        """
        Sample an index for one of the 1000 categories that matches the
        required noun.
        :param noun: The noun from the word_pair
        :return: int of index
        """
        with open(self.folder + '/labels/label_table_v1.csv', mode='r') as f:
            reader = csv.reader(f)
            categories = [rows[1] for rows in reader][1:]
        return npr.choice([i for i in range(1000) if categories[i] == noun])

    def evaluate(self, image_paths):
        """Evaluate image by trying to recognise something in there.
        :param image_paths: The path or paths to the image(s) that is/are to be
            evaluated
        :returns: A value between 0 and 1, the higher the number the better
            the evaluation
        """

        print("Starting evaluation...")
        if type(image_paths) == str:
            image_paths = [image_paths]
        imgs = [imageio.imread(ip) for ip in image_paths]
        imgs = [np.array(cv2.resize(i, (299, 299))) / 255 for i in imgs]
        logits = self.inception_module(dict(images=np.array(imgs)))
        softmax = tf.nn.softmax(logits)
        top_k_values, top_k_indices = tf.nn.top_k(softmax, 3,
                                                  name='top_predictions')
        init = tf.global_variables_initializer()

        # Calculate top k predictions for each picture
        with tf.Session() as sess:
            sess.run(init)
            pics = sess.run(top_k_indices)

        # Fetch the vector representations for each label for each picture
        vecs = []
        for i in pics:
            vecs_sub = []
            for c in i:
                vecs_sub = vecs_sub + [
                    [l[1:] for l in self.vec_list if l[0] == c - 1]]
            vecs = vecs + [vecs_sub]

        # Calculate distances between 3 top predictions for each image,
        # then take the min of those
        dists = []
        # Go through pictures
        for pic in vecs:
            dists_btwn_lbls = []
            # Go through labels
            for l in pic:
                dists_to_othr_lbl = []
                # Go through each word in the label
                for v in l:
                    # And now compare with all other labels and their words
                    for l2 in pic:
                        if l2 != l:
                            for v2 in l2:
                                dists_to_othr_lbl = dists_to_othr_lbl + [np.sqrt(
                                    np.sum((np.array(v) - np.array(v2)) ** 2))]
                dists_btwn_lbls = dists_btwn_lbls + [np.mean(dists_to_othr_lbl)]
            dists = dists + [np.min(dists_btwn_lbls)]

        # Scale from 0 to 1 using (mirrored) sigmoid function with 0.5 at 8.5,
        # lower dists giving higher evals and scaling by 2 to make the
        # transition from 1 to 0 quicker.
        evals = 1 / (1 + np.exp((np.array(dists) - 8.5) * 2))

        return list(evals)

    def load_glove_vecs(self):
        """
        Load the vector representation for certain words from a pretrained
        glove model.
        :return: List of vectors, where the first element of each entry in
            the list is the imagenet class index and the rest are the vector
            entries
        """
        file_content = ''
        with open(self.folder + '/labels/glove_vecs.txt') as f:
            for line in f:
                file_content = file_content + line
        file_content = file_content.replace('\n', '')
        vec_list = file_content.split(']')
        vec_list = [s.replace('[', '') for s in vec_list]
        vec_list = [[float(v) for v in s.split()] for s in vec_list][:-1]
        return vec_list

    def create(self, emotion, word_pairs, number_of_artifacts=10, **kwargs):
        """Create artifacts in the group's domain.

        The given inputs can be parsed and deciphered by the system using any methods available.

        The function should return a list in the form of:

            [
                (artifact1, {"evaluation": 0.76, 'foo': 'bar'}),
                (artifact2, {"evaluation": 0.89, 'foo': 'baz'}),
                # ...
                (artifactn, {"evaluation": 0.29, 'foo': 'bax'})
            ]

        :param str emotion:
            One of "the six basic emotions": anger, disgust, fear, happiness, sadness or surprise.
            The emotion should be perceivable in the output(s).
        :param list word_pairs:
            List of 2-tuples, the word pairs associated with the output(s). The word_pairs are (noun, property) pairings
            where each pair presents a noun and its property which may be visible in the output. (Think of more creative
            ways to present the pairings than literal meaning.)
        :param int number_of_artifacts:
            Number of artifacts returned
        :returns:
            List with *number_of_artifacts* elements. Each element should be (artifact, metadata) pair, where metadata
            should be a dictionary holding at least 'evaluation' keyword with float value.

        """
        print("Group Example create with input args: {} {}".format(emotion,
                                                                   word_pairs))

        ret = [(w, {'evaluation': self.evaluate(w)[0]}) for w in
               [self.generate(emotion, word_pairs) for _ in
                range(number_of_artifacts)]]

        print('-' * 100)
        print('-' * 100)

        print(ret)
        print('-' * 100)
        print('-' * 100)
        return ret
