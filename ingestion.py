import rawpy
import torch

def load_srf_to_tensor(srf_path):
    with rawpy.imread(srf_path) as raw:
        # Extract unprocessed 2D Bayer pattern array
        raw_array = raw.raw_image_visible.astype('float32')
        
        # Normalize 14-bit Sony sensor values (0-16383) to [0.0, 1.0]
        max_val = float(raw.white_level)
        normalized = raw_array / max_val
        
    # Output shape: [1, 1, H, W] tensor for 2D Conv layers
    return torch.from_numpy(normalized).unsqueeze(0).unsqueeze(0)
