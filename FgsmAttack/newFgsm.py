import torch
from torch.autograd import Variable
from torchvision import models
import torch.nn as nn
from torchvision import transforms
import os
import numpy as np
import cv2
import argparse
from FgsmAttack.imagenet_labels import classes


def nothing(x):
    pass


def fgsmAttack(image_path="goldfish.jpg", eps=20):
    image_path = "FgsmAttack/images/"+image_path
    model_name = "resnet18"
    IMG_SIZE = 224

    print()
    print('Model: %s' % (model_name))
    print('Image: %s' % (image_path))
    print("Epsilon Value: %d" % (eps))
    print()

    orig = cv2.imread(image_path)[..., ::-1]
    orig = cv2.resize(orig, (IMG_SIZE, IMG_SIZE))
    img = orig.copy().astype(np.float32)
    perturbation = np.empty_like(orig)

    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    img /= 255.0
    img = (img - mean)/std
    img = img.transpose(2, 0, 1)

    model = getattr(models, model_name)(pretrained=True)
    model.eval()
    criterion = nn.CrossEntropyLoss()

    device = 'cpu'

    # prediction before attack
    inp = Variable(torch.from_numpy(img).to(
        device).float().unsqueeze(0), requires_grad=True)

    out = model(inp)
    pred = np.argmax(out.data.cpu().numpy())
    # print('Prediction before attack: %s' % (classes[pred].split(',')[0]))

    out = model(inp)
    loss = criterion(out, Variable(
        torch.Tensor([float(pred)]).to(device).long()))

    loss.backward()

    inp.data = inp.data + ((eps/255.0) * torch.sign(inp.grad.data))
    inp.grad.data.zero_()  # unnecessary

    # predict on the adversarial image
    pred_adv = np.argmax(model(inp).data.cpu().numpy())
    # print("After attack: eps [%f] \t%s"
    #         %(eps, classes[pred_adv].split(',')[0]), end="\r")#, end='\r')#'eps:', eps, end='\r')

    # return classes[pred_adv]
    adv = inp.data.cpu().numpy()[0]
    # cv2.normalize((adv - img).transpose(1, 2, 0), perturbation, 0, 255, cv2.NORM_MINMAX, 0)
    perturbation = (adv - img).transpose(1, 2, 0)
    adv = adv.transpose(1, 2, 0)
    adv = (adv * std) + mean
    adv = adv * 255.0
    adv = adv[..., ::-1]
    adv = np.clip(adv, 0, 255).astype(np.uint8)
    perturbation = perturbation * 255
    perturbation = np.clip(perturbation, 0, 255).astype(np.uint8)
    cv2.imwrite("./FgsmAttack/fgsmAdversarial.jpg", adv)
    cv2.imwrite("./FgsmAttack/perbutation.jpg", perturbation)
    cv2.imwrite("./static/images/fgsmattack/fgsmAdversarial.jpg", adv)
    cv2.imwrite("./static/images/fgsmattack/perbutation.jpg", perturbation)

    print("Classification: ", classes[pred_adv])
    print()
    return classes[pred_adv]

    # cv2.imshow(window_adv, perturbation)
    # cv2.imshow('adversarial image', adv)
    # key = cv2.waitKey(500) & 0xFF
    # if key == 27:
    #     break
    # elif key == ord('s'):
    #     cv2.imwrite('img_adv.png', adv)
    #     cv2.imwrite('perturbation.png', perturbation)
    # print()
    # cv2.destroyAllWindows()


# if __name__ == '__main__':
#     print(fgsmAttack())
