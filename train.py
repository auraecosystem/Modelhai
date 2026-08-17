import torch
import torch.nn as nn
from torch.utils.data import DataLoader

class CharbonnierLoss(nn.Module):
    """Smooth L1 Loss variant optimal for image restoration tasks."""
    def __init__(self, eps=1e-3):
        super().__init__()
        self.eps2 = eps ** 2

    def forward(self, x, y):
        return torch.mean(torch.sqrt((x - y) ** 2 + self.eps2))

def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0

    for inputs, targets in dataloader:
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)

    return running_loss / len(dataloader.dataset)

@torch.no_grad()
def validate(model, dataloader, criterion, device):
    model.eval()
    val_loss = 0.0

    for inputs, targets in dataloader:
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        val_loss += loss.item() * inputs.size(0)

    return val_loss / len(dataloader.dataset)

def run_training(train_raw, train_rgb, val_raw, val_rgb, epochs=50, batch_size=8, lr=1e-4):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")

    train_loader = DataLoader(RawToRgbDataset(train_raw, train_rgb), batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(RawToRgbDataset(val_raw, val_rgb), batch_size=batch_size, shuffle=False, num_workers=4)

    model = RawUNet(in_channels=4, out_channels=3).to(device)
    criterion = CharbonnierLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float('inf')

    for epoch in range(1, epochs + 1):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = validate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Epoch [{epoch:02d}/{epochs:02d}] | Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 'best_raw_unet.pth')

# Example execution:
# run_training(train_raw_list, train_rgb_list, val_raw_list, val_rgb_list)
