import tensorflow as tf
from tensorflow.keras import layers
import numpy as np

class AttentionLayer(layers.Layer):
    def __init__(self, attention, d_model, n_heads, d_keys=None, d_values=None):
        super(AttentionLayer, self).__init__()

        d_keys = d_keys or (d_model // n_heads)
        d_values = d_values or (d_model // n_heads)

        self.inner_attention = attention
        self.query_projection = layers.Dense(d_keys * n_heads)
        self.key_projection = layers.Dense(d_keys * n_heads)
        self.value_projection = layers.Dense(d_values * n_heads)
        self.out_projection = layers.Dense(d_model)
        self.n_heads = n_heads
        

    def call(self, queries, keys, values, attn_mask, tau=None, delta=None):
        B, L, _ = queries.shape
        _, S, _ = keys.shape
        H = self.n_heads
        
        querie_reshape = layers.Reshape((L, H, -1))
        keys_reshape = layers.Reshape((S, H, -1))
        values_reshape = layers.Reshape((S, H, -1))
        
        queries = querie_reshape(self.query_projection(queries))
        keys = keys_reshape(self.key_projection(keys))
        values = values_reshape(self.value_projection(values))

      #  queries = tf.reshape(self.query_projection(queries), (B, L, H, -1))
      #  keys = tf.reshape(self.key_projection(keys), (B, S, H, -1))
       # values = tf.reshape(self.value_projection(values), (B, S, H, -1))

        out, attn = self.inner_attention(
            queries,
            keys,
            values,
            attn_mask,
            tau=tau,
            delta=delta
        )
        #out = tf.reshape(out, (B, L, -1))
        out_reshape = layers.Reshape((L, -1))
        out = out_reshape(out)
        #print("shape our pre-out_projection:", out.shape)
        return self.out_projection(out), attn
    
class FullAttention(layers.Layer):
    def __init__(self, mask_flag=True, factor=5, scale=None, attention_dropout=0.1, output_attention=False):
        super(FullAttention, self).__init__()
        self.scale = scale
        self.mask_flag = mask_flag
        self.output_attention = output_attention
        self.dropout = tf.keras.layers.Dropout(attention_dropout)

    def call(self, queries, keys, values, attn_mask, tau=None, delta=None):
        B, L, H, E = queries.shape
        _, S, _, D = values.shape
        scale = self.scale or 1. / np.sqrt(E)

        scores = tf.einsum("blhe,bshe->bhls", queries, keys)

        if self.mask_flag:
            if attn_mask is None:
                attn_mask = TriangularCausalMask(B, L, device=queries.device)  

            scores = tf.where(attn_mask.mask, -np.inf, scores)

        A = self.dropout(tf.nn.softmax(scale * scores, axis=-1))
        V = tf.einsum("bhls,bshd->blhd", A, values)

        if self.output_attention:
            return (V, A)
        else:
            return (V, None)

class TriangularCausalMask(tf.Module):
    def __init__(self, B, L):
        mask_shape = [B, 1, L, L]
        self._mask = tf.linalg.band_part(tf.ones(mask_shape, dtype=tf.bool), -1, 0)

    @property
    def mask(self):
        return self._mask