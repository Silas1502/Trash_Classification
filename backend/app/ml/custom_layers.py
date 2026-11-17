from keras import layers, ops, saving


def _l2_normalize(values, axis):
    squared_norm = ops.sum(ops.square(values), axis=axis, keepdims=True)
    return values * ops.rsqrt(ops.maximum(squared_norm, 1e-12))


@saving.register_keras_serializable(package="CustomLayers", name="CosineDense")
class CosineDense(layers.Layer):
    def __init__(self, units, scale=20.0, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.scale = scale

    def build(self, input_shape):
        self.kernel = self.add_weight(
            name="kernel", shape=(input_shape[-1], self.units),
            initializer="glorot_uniform", trainable=True,
        )

    def call(self, inputs):
        norm_inputs = _l2_normalize(inputs, axis=-1)
        norm_kernel = _l2_normalize(self.kernel, axis=0)
        return self.scale * ops.matmul(norm_inputs, norm_kernel)

    def get_config(self):
        return {**super().get_config(), "units": self.units, "scale": self.scale}


@saving.register_keras_serializable(package="TrashClassification")
class L2Normalize(layers.Layer):
    def call(self, inputs, mask=None):
        return _l2_normalize(inputs, axis=-1)
