# stdlib
from pathlib import Path
from collections import OrderedDict
# 3p
from tqdm import tqdm
import cv2
import torch
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
# project
from .craft import CRAFT
from .craft_utils import getDetBoxes, adjustResultCoordinates
from .imgproc import resize_aspect_ratio, normalizeMeanVariance


class TextDetector:
    def __init__(self, text_threshold=0.7, low_text=0.4, link_threshold=0.4, canvas_size=1280, mag_ratio=1.5):
        self.text_threshold = text_threshold
        self.low_text = low_text
        self.link_threshold = link_threshold
        self.canvas_size = canvas_size
        self.mag_ratio = mag_ratio

        # load model
        self.net = CRAFT()
        weights = Path(__file__).absolute().parent / 'weights/craft_mlt_25k.pth'
        self.cuda = torch.cuda.is_available()
        if self.cuda:
            self.net.load_state_dict(self.copyStateDict(torch.load(weights)))
            self.net = self.net.cuda()
            self.net = torch.nn.DataParallel(self.net)
            cudnn.benchmark = False
        else:
            self.net.load_state_dict(self.copyStateDict(torch.load(weights, map_location='cpu')))

        self.net.eval()

    def detect(self, imgs):
        return [self.test_net(img) for img in tqdm(imgs, desc="Detecting text")]

    def test_net(self, image):
        # resize
        img_resized, target_ratio, size_heatmap = resize_aspect_ratio(
            image, self.canvas_size, interpolation=cv2.INTER_LINEAR, mag_ratio=self.mag_ratio)
        ratio_h = ratio_w = 1 / target_ratio

        # preprocessing
        x = normalizeMeanVariance(img_resized)
        x = torch.from_numpy(x).permute(2, 0, 1)    # [h, w, c] to [c, h, w]
        x = Variable(x.unsqueeze(0))                # [c, h, w] to [b, c, h, w]
        if self.cuda:
            x = x.cuda()

        # forward pass
        with torch.no_grad():
            y, feature = self.net(x)

        # make score and link map
        score_text = y[0, :, :, 0].cpu().data.numpy()
        score_link = y[0, :, :, 1].cpu().data.numpy()

        # Post-processing
        boxes, polys = getDetBoxes(score_text, score_link, self.text_threshold, self.link_threshold, self.low_text, poly=True)

        # coordinate adjustment
        boxes = adjustResultCoordinates(boxes, ratio_w, ratio_h)
        polys = adjustResultCoordinates(polys, ratio_w, ratio_h)
        for k in range(len(polys)):
            if polys[k] is None:
                polys[k] = boxes[k]

        return boxes, polys

    def copyStateDict(self, state_dict):
        if list(state_dict.keys())[0].startswith("module"):
            start_idx = 1
        else:
            start_idx = 0
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = ".".join(k.split(".")[start_idx:])
            new_state_dict[name] = v
        return new_state_dict
