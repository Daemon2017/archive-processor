import numpy as np
import os
import scipy.misc

from skimage.io import imread

from keras.models import Model
from keras.layers import Conv2D, MaxPooling2D, Input, concatenate, Conv2DTranspose, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import TensorBoard, ModelCheckpoint, Callback
from keras import backend as K

K.set_image_dim_ordering('tf')

img_width = 1216
img_height = 800

def dice_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2.0 * intersection + 1.0) / (K.sum(y_true_f) + K.sum(y_pred_f) + 1.0)


def dice_coef_loss(y_true, y_pred):
    return -dice_coef(y_true, y_pred)


def build():
    print('Building model...')
    inputs = Input(shape=(img_height, img_width, 3))

    conv1 = Conv2D(32, (3, 3), activation='elu', padding='same')(inputs)
    conv1 = Conv2D(32, (3, 3), activation='elu', padding='same')(conv1)
    drop1 = Dropout(0.05)(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(drop1)
    conv2 = Conv2D(64, (3, 3), activation='elu', padding='same')(pool1)
    conv2 = Conv2D(64, (3, 3), activation='elu', padding='same')(conv2)
    drop2 = Dropout(0.05)(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(drop2)
    conv3 = Conv2D(128, (3, 3), activation='elu', padding='same')(pool2)
    conv3 = Conv2D(128, (3, 3), activation='elu', padding='same')(conv3)
    drop3 = Dropout(0.05)(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(drop3)
    conv4 = Conv2D(256, (3, 3), activation='elu', padding='same')(pool3)
    conv4 = Conv2D(256, (3, 3), activation='elu', padding='same')(conv4)
    drop4 = Dropout(0.05)(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(drop4)
    conv5 = Conv2D(512, (3, 3), activation='elu', padding='same')(pool4)
    conv5 = Conv2D(512, (3, 3), activation='elu', padding='same')(conv5)
    drop5 = Dropout(0.05)(conv5)
    pool5 = MaxPooling2D(pool_size=(2, 2))(drop5)

    conv6 = Conv2D(1024, (3, 3), activation='elu', padding='same')(pool5)
    conv6 = Conv2D(1024, (3, 3), activation='elu', padding='same')(conv6)
    drop6 = Dropout(0.05)(conv6)

    up7 = concatenate([Conv2DTranspose(512, (2, 2), strides=(2, 2), padding='same')(drop6), conv5], axis=3)
    conv7 = Conv2D(512, (3, 3), activation='elu', padding='same')(up7)
    conv7 = Conv2D(512, (3, 3), activation='elu', padding='same')(conv7)
    drop7 = Dropout(0.05)(conv7)
    up8 = concatenate([Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(drop7), conv4], axis=3)
    conv8 = Conv2D(256, (3, 3), activation='elu', padding='same')(up8)
    conv8 = Conv2D(256, (3, 3), activation='elu', padding='same')(conv8)
    drop8 = Dropout(0.05)(conv8)
    up9 = concatenate([Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(drop8), conv3], axis=3)
    conv9 = Conv2D(128, (3, 3), activation='elu', padding='same')(up9)
    conv9 = Conv2D(128, (3, 3), activation='elu', padding='same')(conv9)
    drop9 = Dropout(0.05)(conv9)
    up10 = concatenate([Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(drop9), conv2], axis=3)
    conv10 = Conv2D(64, (3, 3), activation='elu', padding='same')(up10)
    conv10 = Conv2D(64, (3, 3), activation='elu', padding='same')(conv10)
    drop10 = Dropout(0.05)(conv10)
    up11 = concatenate([Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(drop10), conv1], axis=3)
    conv11 = Conv2D(32, (3, 3), activation='elu', padding='same')(up11)
    conv11 = Conv2D(32, (3, 3), activation='elu', padding='same')(conv11)
    drop11 = Dropout(0)(conv11)

    conv12 = Conv2D(1, (1, 1), activation='sigmoid')(drop11)

    model = Model(inputs=[inputs], outputs=[conv12])

    model.compile(optimizer=Adam(lr=0.0001), loss=dice_coef_loss, metrics=[dice_coef])
    print('Model ready!')
    return model


def predict():
    print('Preparing prediction set...')
    files = os.listdir('./predict_raws/')
    x_files_names = filter(lambda x: x.endswith('_raw.jpg'), files)
    total = len(x_files_names)

    x_predict = np.ndarray((total, img_height, img_width, 3), dtype=np.uint8)
    i = 0
    for x_file_name in x_files_names:
        img = imread(os.path.join('./predict_raws/' + x_file_name))
        x_predict[i] = np.array([img])
        i += 1
    print('Prediction set prepared!')

    x_predict = x_predict.astype('float32')
    x_mean = np.mean(x_predict)
    x_std = np.std(x_predict)
    x_predict -= x_mean
    x_predict /= x_std

    predictions = model.predict_on_batch(x_predict)
    i = 0
    for prediction in predictions:
        prediction = (prediction[:, :, 0] * 255.).astype(np.uint8)
        short_name = os.path.splitext(x_files_names[i])[0]
        scipy.misc.imsave('./predict_masks/' + str(short_name) + '_mask.png', prediction)
        i += 1


if not os.path.exists('predict_raws'):
    os.makedirs('predict_raws')

if not os.path.exists('predict_masks'):
    os.makedirs('predict_masks')

model = build()
model.load_weights('weights_batch.h5')

thrd_choice = raw_input('Start prediction? (y or n): ')
if thrd_choice == 'y':
    predict()
