import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class MLPBlock(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim, drop_rate):
        super(MLPBlock, self).__init__()
        self.in_linear = nn.Linear(in_dim, hidden_dim)
        self.dropout = nn.Dropout(drop_rate)
        self.out_linear = nn.Linear(hidden_dim, out_dim)
        self.ln = nn.LayerNorm(out_dim)

    def forward(self, x):
        '''
        x: [B, *, in_dim]
        '''
        out = self.in_linear(x)
        out = F.relu(out)
        out = self.dropout(out)
        out = self.out_linear(out)
        out = self.ln(self.dropout(out) + x)
        return out


class AttentionPooling(nn.Module):
    """
    P_sem: aggregates the cycle representation sequence H into a global query q. (Eq. 6)
    """
    def __init__(self, d_model):
        super(AttentionPooling, self).__init__()
        self.query = nn.Parameter(torch.randn(d_model) / math.sqrt(d_model))
        self.d_model = d_model

    def forward(self, H, mask):
        '''
        H: [B, S, d], mask: [B, S] (1 for observed cycles, 0 for padding)
        '''
        scores = torch.matmul(H, self.query) / math.sqrt(self.d_model)  # [B, S]
        scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = torch.softmax(scores, dim=-1)  # [B, S]
        q = torch.sum(attn.unsqueeze(-1) * H, dim=1)  # [B, d]
        return q


class TemporalScaleBlock(nn.Module):
    """
    One N-HiTS-inspired scale-specific branch: masked average pooling P_l with
    factor pool_factor followed by a nonlinear block F_l. (Eqs. 11-12)
    """
    def __init__(self, seq_len, pool_factor, d_model, d_ff, drop_rate):
        super(TemporalScaleBlock, self).__init__()
        self.pool_factor = pool_factor
        self.pooled_len = math.ceil(seq_len / pool_factor)
        self.block = nn.Sequential(
            nn.Flatten(start_dim=1),
            nn.Linear(self.pooled_len * d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(drop_rate),
            nn.Linear(d_ff, d_model),
        )

    def forward(self, H, mask):
        '''
        H: [B, S, d], mask: [B, S]
        '''
        masked = (H * mask.unsqueeze(-1)).transpose(1, 2)  # [B, d, S]
        if self.pool_factor > 1:
            num = F.avg_pool1d(masked, self.pool_factor, ceil_mode=True, count_include_pad=False)
            cnt = F.avg_pool1d(mask.unsqueeze(1), self.pool_factor, ceil_mode=True, count_include_pad=False)
            pooled = num / cnt.clamp(min=1e-8)  # masked mean within each window
        else:
            pooled = masked
        return self.block(pooled.transpose(1, 2))  # [B, d]


class Model(nn.Module):
    """
    Dual-Axis Semantic-Temporal Basis Fusion for battery lifetime prediction.

    A CyclePatch-style cycle encoder maps each cycle to a latent vector, giving
    H = [h_1, ..., h_S]. H is then processed along two axes:
      - Semantic axis: attention pooling -> global query q -> attention over K
        learnable semantic bases -> global semantic representation s. (Eqs. 6-10)
      - Temporal axis: M multi-scale pooled N-HiTS-inspired blocks -> temporal
        bases {t_1, ..., t_M}. (Eqs. 11-13)
    The semantic representation gates the temporal scales (Eqs. 15-18), and both
    axes are combined via cross-axis bilinear fusion (Eqs. 20-22) before the
    prediction MLP (Eq. 24).
    """

    def __init__(self, configs):
        super(Model, self).__init__()
        self.d_model = configs.d_model
        self.d_ff = configs.d_ff
        self.charge_discharge_length = configs.charge_discharge_length
        self.early_cycle_threshold = configs.early_cycle_threshold
        self.drop_rate = configs.dropout
        self.e_layers = configs.e_layers
        self.num_semantic_bases = getattr(configs, 'num_semantic_bases', 4)  # K
        self.pool_factors = getattr(configs, 'pool_factors', [1, 2, 4])  # one per temporal scale

        # Cycle encoder E_cyc (CyclePatch-style): each cycle is one patch
        self.intra_flatten = nn.Flatten(start_dim=2)
        self.intra_embed = nn.Linear(self.charge_discharge_length * 3, self.d_model)
        self.intra_MLP = nn.ModuleList([MLPBlock(self.d_model, self.d_ff, self.d_model, self.drop_rate) for _ in range(configs.e_layers)])

        # Semantic branch
        self.sem_pooling = AttentionPooling(self.d_model)
        self.semantic_bases = nn.Parameter(torch.randn(self.num_semantic_bases, self.d_model) / math.sqrt(self.d_model))  # B_sem

        # Temporal branch
        self.temporal_blocks = nn.ModuleList([
            TemporalScaleBlock(self.early_cycle_threshold, p, self.d_model, self.d_ff, self.drop_rate)
            for p in self.pool_factors
        ])

        # Semantic-conditioned scale gating: w = Softmax(W_w s + b_w)
        self.scale_gate = nn.Linear(self.d_model, len(self.pool_factors))

        # Cross-axis bilinear fusion: z_int = (W_s s) * (W_t t)
        self.W_s = nn.Linear(self.d_model, self.d_model, bias=False)
        self.W_t = nn.Linear(self.d_model, self.d_model, bias=False)

        # Prediction MLP g_pred over z_fuse = [s; t; z_int]
        self.head = nn.Sequential(
            nn.Linear(3 * self.d_model, self.d_ff),
            nn.ReLU(),
            nn.Dropout(self.drop_rate),
            nn.Linear(self.d_ff, configs.output_num),
        )

    def encode_cycles(self, cycle_curve_data):
        '''
        cycle_curve_data: [B, early_cycle, fixed_len, num_var] -> H: [B, early_cycle, d_model]
        '''
        x = self.intra_flatten(cycle_curve_data)  # [B, early_cycle, fixed_len * num_var]
        x = self.intra_embed(x)
        for i in range(self.e_layers):
            x = self.intra_MLP[i](x)
        return x

    def forward(self, cycle_curve_data, curve_attn_mask, return_embedding=False):
        '''
        cycle_curve_data: [B, early_cycle, fixed_len, num_var]
        curve_attn_mask: [B, early_cycle]
        '''
        mask = curve_attn_mask.float()
        H = self.encode_cycles(cycle_curve_data)  # [B, S, d]

        # Semantic axis: q -> alpha -> s
        q = self.sem_pooling(H, mask)  # [B, d]
        alpha = torch.softmax(torch.matmul(q, self.semantic_bases.t()) / math.sqrt(self.d_model), dim=-1)  # [B, K]
        s = torch.matmul(alpha, self.semantic_bases)  # [B, d]

        # Temporal axis: multi-scale temporal bases {t_1, ..., t_M}
        t_scales = torch.stack([blk(H, mask) for blk in self.temporal_blocks], dim=1)  # [B, M, d]

        # Semantic-conditioned temporal aggregation
        w = torch.softmax(self.scale_gate(s), dim=-1)  # [B, M]
        t = torch.sum(w.unsqueeze(-1) * t_scales, dim=1)  # [B, d]

        # Cross-axis bilinear fusion
        z_int = self.W_s(s) * self.W_t(t)  # [B, d]
        z_fuse = torch.cat([s, t, z_int], dim=-1)  # [B, 3d]

        preds = self.head(z_fuse)
        if return_embedding:
            return preds, z_fuse
        return preds

    def diversity_loss(self):
        '''
        Soft diversity regularization on the semantic bases (Eq. 26); add to the
        prediction loss as L = L_pred + lambda_div * L_div.
        '''
        K = self.num_semantic_bases
        normed = F.normalize(self.semantic_bases, dim=-1)
        cos = torch.matmul(normed, normed.t())  # [K, K]
        off_diag = cos - torch.diag_embed(torch.diagonal(cos))
        return (off_diag ** 2).sum() / (K * (K - 1))
