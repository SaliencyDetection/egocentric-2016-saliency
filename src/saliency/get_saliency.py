'''
To run the script:
jpan@nx2:~>> export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/opt/caffe-2015-10/lib
jpan@nx2:~>> THEANO_FLAGS='floatX=float32,device=gpu,nvcc.fastmath=True' 
            CUDA_ROOT=/usr/local/cuda srun -w c7 --pty --gres=gpu:1  python get_saliency.py
'''

import os
import numpy as np
import cPickle as pickle
from scipy import misc
import scipy.io
from scipy.misc import imsave,imresize
from scipy import ndimage
from skimage import io
from __init__ import SalNet
import glob
import cv2
from lasagne import layers
from lasagne.updates import nesterov_momentum
from nolearn.lasagne import NeuralNet,BatchIterator
import theano

specfile = '/imatge/mcherto/examples/deploy.prototxt'
modelfile = '/imatge/mcherto/examples/model.caffemodel'

def get_saliency_for_salnet(image_url,sal_url):
    salnet = SalNet(specfile,modelfile)
    arr_files = glob.glob(image_url+"*.png")
    for i in range(len(arr_files)):  
        url_image = arr_files[i]
        img = io.imread(url_image)       
        img = np.asarray(img, dtype = 'float32')
        if len(img.shape) == 2:
            img = to_rgb(img)
        sal_map = salnet.get_saliency(img)
        #saliency = misc.imresize(y,(img.shape[0],img.shape[1]))
        aux = url_image.split("/")[-1].split(".")[0]
        misc.imsave(sal_url+'/'+aux+'.png', sal_map)

class FlipBatchIterator(BatchIterator):
    def transform(self, Xb, yb):
        Xb, yb = super(FlipBatchIterator, self).transform(Xb, yb)

        # Flip half of the images in this batch at random:
        bs = Xb.shape[0]
        indices = np.random.choice(bs, bs / 2, replace=False)
        Xb[indices] = Xb[indices, :, :, ::-1]
        tmp =  yb[indices].reshape(bs/2,1,48,48)
        mirror = tmp[ :,:,:, ::-1]
        yb[indices] =  mirror.reshape(bs/2,48*48)
        return Xb, yb

class AdjustVariable(object):
    def __init__(self, name, start=0.03, stop=0.001):
        self.name = name
        self.start, self.stop = start, stop
        self.ls = None

    def __call__(self, nn, train_history):
        if self.ls is None:
            self.ls = np.linspace(self.start, self.stop, nn.max_epochs)

        epoch = train_history[-1]['epoch']
        new_value = float32(self.ls[epoch - 1])
        getattr(nn, self.name).set_value(new_value)

def to_rgb(im):
    im.resize((96, 96, 1), refcheck=False)
    return np.repeat(im.astype(np.float32), 3, 2)

def get_saliency_for_juntingnet(image_url,sal_url):
    arr_files = glob.glob(image_url+"*.png")
    for i in range(len(arr_files)):  
        url_image = arr_files[i]
        image = io.imread(url_image)       
        img = misc.imresize(image,(96,96))
        img = np.asarray(img, dtype = 'float32') / 255.
        img = img.transpose(2,0,1).reshape(3, 96, 96)
        xt = np.zeros((1, 3, 96, 96), dtype='float32')
        xt[0]=img
        y = juntingnet.predict(xt)
        tmp = y.reshape(48,48)
        blured= ndimage.gaussian_filter(tmp, sigma=3)
        sal_map = cv2.resize(tmp,(image.shape[1],image.shape[0]))
        sal_map -= np.min(sal_map)
        sal_map /= np.max(sal_map)
        #saliency = misc.imresize(y,(img.shape[0],img.shape[1]))
        aux = url_image.split("/")[-1].split(".")[0]
        misc.imsave(sal_url+'/'+aux+'.png', sal_map)

JUNTINGNET_DIR = '/imatge/mcherto/examples/net_128_hidden.pickle'
f = open(JUNTINGNET_DIR, 'rb')
juntingnet = pickle.load(f)
f.close()

def main():
    get_saliency_for_salnet('/imatge/mcherto/input_directory','/imatge/mcherto/output_directory')
    get_saliency_for_juntingnet('/imatge/mcherto/input_directory/','/imatge/mcherto/output_directory')

if __name__ == '__main__':
    main()









