class Configurator:
    def __init__(self):
        self.seq_len = 512
        self.pred_len = 64
        self.output_attention = True
        self.dropout = 0.1
        self.d_model = 512
        self.factor = 1
        self.n_heads = 8
        self.d_ff = 2048
        self.activation = 'gelu'
        self.e_layers = 2
        self.use_amp = True
        self.use_norm = True
