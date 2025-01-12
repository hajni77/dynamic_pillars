from model import PointPillars
import torch
# model parameters



def compute_params(model):
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total_params, trainable_params


if __name__ == '__main__':
    model = PointPillars(3).cuda()
    state_dict = torch.load('/home/ubuntu/.ssh/pillar_logs_last/checkpoints/epoch_40.pth')
    model.load_state_dict(state_dict)
    total_params, trainable_params = compute_params(model)
    print(f"Total params: {total_params}, Trainable params: {trainable_params}")
    
    
    # Total params: 22020872, Trainable params: 22020872