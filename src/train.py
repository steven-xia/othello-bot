"""
The `shifted_leaky_relu()` was found from my private testing to be a very good activation function:
Information can be found here: https://colab.research.google.com/drive/1QJJ9DprXPs5IvCjwQhi5hGiu9CFK999N
"""

import tensorflow


def shifted_leaky_relu(x):
    x = tensorflow.keras.backend.maximum(0.5 * x, x)
    x = tensorflow.keras.backend.maximum(-tensorflow.keras.backend.ones_like(x), x)
    return x


ACTIVATION_FUNCTION = shifted_leaky_relu
DATA_FILE = "networks/training_data.txt"

if __name__ == "__main__":
    import multiprocessing

    import numpy

    import networks.datafile_manager
    import networks.train_utils

    CPU_COUNT = multiprocessing.cpu_count()

    print(f"Loading data from file: {DATA_FILE} ... ")
    data = networks.datafile_manager.load_data(DATA_FILE)

    print(f"Preprocessing data with {CPU_COUNT} threads ... ")
    print(f"  - Parsing data ... ")
    p = multiprocessing.Pool(CPU_COUNT)
    data = p.map(networks.train_utils.preprocess_game, data.items(), chunksize=int(len(data) / CPU_COUNT))

    print(f"  - Splitting data ... ")
    training_inputs, training_outputs = tuple(zip(*data))
    training_board_inputs, training_extra_inputs = tuple(zip(*training_inputs))

    training_board_inputs = numpy.array(training_board_inputs)
    training_extra_inputs = numpy.array(training_extra_inputs)
    training_outputs = numpy.array(training_outputs)

    # TRAINING BELOW ---------------------------------------------------------------------------------------------------

    ACTIVATION = shifted_leaky_relu
    DROPOUT_RATE = 0.2

    board_input = tensorflow.keras.layers.Input(shape=(8, 8, 2))
    extra_input = tensorflow.keras.layers.Input(shape=(2,))

    x = board_input

    x = tensorflow.keras.layers.Conv2D(filters=8, kernel_size=(3, 3), strides=(1, 1), padding="same", use_bias=True,
                                       kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)

    x = tensorflow.keras.layers.Conv2D(filters=8, kernel_size=(3, 3), strides=(1, 1), padding="same", use_bias=True,
                                       kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)

    x = tensorflow.keras.layers.Conv2D(filters=8, kernel_size=(2, 2), strides=(2, 2), padding="valid", use_bias=True,
                                       kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)
    x = tensorflow.keras.layers.Dropout(DROPOUT_RATE)(x)

    x = tensorflow.keras.layers.Conv2D(filters=16, kernel_size=(3, 3), strides=(1, 1), padding="same", use_bias=True,
                                       kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)

    x = tensorflow.keras.layers.Conv2D(filters=16, kernel_size=(3, 3), strides=(1, 1), padding="same", use_bias=True,
                                       kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)

    x = tensorflow.keras.layers.Conv2D(filters=16, kernel_size=(2, 2), strides=(2, 2), padding="valid", use_bias=True,
                                       kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)
    x = tensorflow.keras.layers.Dropout(DROPOUT_RATE)(x)

    x = tensorflow.keras.layers.Flatten()(x)
    x = tensorflow.keras.layers.Concatenate()([x, extra_input])

    x = tensorflow.keras.layers.Dense(units=64, use_bias=True, kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)
    x = tensorflow.keras.layers.Dropout(DROPOUT_RATE)(x)

    x = tensorflow.keras.layers.Dense(units=64, use_bias=True, kernel_initializer="glorot_normal")(x)
    x = tensorflow.keras.layers.Activation(ACTIVATION)(x)
    x = tensorflow.keras.layers.BatchNormalization()(x)
    x = tensorflow.keras.layers.Dropout(DROPOUT_RATE)(x)

    network_output = tensorflow.keras.layers.Dense(units=1, activation=tensorflow.keras.activations.tanh,
                                                   use_bias=True, kernel_initializer="glorot_normal")(x)

    network = tensorflow.keras.models.Model(inputs=[board_input, extra_input], outputs=network_output)
    network.compile(
        tensorflow.keras.optimizers.Adam(),
        loss=tensorflow.keras.losses.mse,
    )

    network.summary()

    network.fit(
        x=[training_board_inputs, training_extra_inputs],
        y=training_outputs,
        epochs=32,
        validation_split=0.01,
        batch_size=256,
        callbacks=[
            tensorflow.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=1, verbose=1,
                                                         mode='auto', min_delta=0.0001, cooldown=0, min_lr=0),
            tensorflow.keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=2, verbose=1,
                                                     mode='auto', baseline=None, restore_best_weights=True)
        ],
        verbose=True
    )
