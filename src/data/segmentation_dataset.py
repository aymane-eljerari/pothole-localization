import os
import random

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
import torchvision.transforms.functional as TF


# Link to dataset: https://sites.google.com/view/pothole-600/dataset
class SegmentationDataset(Dataset):
    '''Pothole Segmentation Dataset dataset.'''

    def __init__(self, raw_data_path=None, data_path=None, label_path=None):
        '''
        Args:
            path                (string):                       directory containing all images
            feature_exctractor  (SegformerFeatureExtractor):    Segformer input encoder from Hugging Face
        '''

        if (raw_data_path == None) and (data_path != None) and (label_path != None):
            self.data_augment   = torch.load(data_path)
            self.label_augment  = torch.load(label_path)
            # Get size of dataset
            data_augment_num    = os.path.basename(os.path.dirname(data_path))[-2:]
            label_augment_num   = os.path.basename(os.path.dirname(label_path))[-2:]

            assert data_augment_num == label_augment_num

            self.length = 600*int(data_augment_num)

        else:
            self.angles             = [-75, -60, -45, -30, -15, 15, 30, 45, 60, 75]
            self.augment_num        = len(self.angles)+1
            self.length             = 600*(self.augment_num)

            self.raw_path           = raw_data_path
            self.store_path         = f'/home/aymane/School/pothole-localization/data/segmentation/augment_{self.augment_num}'

            self.data_path          = os.path.join(self.raw_path, 'rgb')
            self.label_path         = os.path.join(self.raw_path, 'label')

            self.data               = torch.zeros((600, 3, 384, 384), dtype=torch.int8)
            self.label              = torch.zeros((600, 1, 384, 384), dtype=torch.int8)

            self.create_directories()
            self.generate_data()

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        return self.data_augment[idx], self.label_augment[idx]
 

    def generate_data(self):
        #TODO: dont forget random seed initialization for data transforms
        '''
        Generates and stores the data and labels
        '''

        # Generate Initial Dataset
        for i in range(600):
            img             = Image.open(os.path.join(self.data_path, str(i+1) + '.png'))
            label           = Image.open(os.path.join(self.label_path, str(i+601) + '.png')).convert('L')

            transform       = transforms.Compose([transforms.PILToTensor(), transforms.Resize(384)])
            img_tensor      = transform(img).detach().clone().squeeze_()
            label_tensor    = transform(label).detach().clone().squeeze_()

            self.data[i]    = img_tensor
            self.label[i]   = label_tensor/255

        del img, label, img_tensor, label_tensor
        
        # Data Augmentation
        self.data_  = torch.cat((self.data, torch.cat([self.angle_rotation(i) for i in self.data])))
        self.label_ = torch.cat((self.label, torch.cat([self.angle_rotation(i) for i in self.label])))

        self.save_pickle(self.data_, self.store_path, 'data.pt')
        self.save_pickle(self.label_, self.store_path, 'label.pt')
        
        del self.data_, self.label_, self.data, self.label

        self.concatenate_data()

    def concatenate_data(self):
        self.data_augment   = torch.empty((self.length, 3, 384, 384), dtype=torch.int8)
        self.label_augment  = torch.empty((self.length, 1, 384, 384), dtype=torch.int8)

        for i, filename in enumerate(os.listdir(self.store_path), start=1):
            f = os.path.join(self.store_path, filename)
            tensor = torch.load(f)
            if filename[0] == 'd':
                self.data_augment = tensor
            if filename[0] == 'l':
                self.label_augment = tensor

    def angle_rotation(self, image):
        '''
            Args:
                    image       (Tensor):   input image as tensor
        '''
        images = torch.empty(size=(len(self.angles), TF.get_image_num_channels(image), 384, 384))
        count = 0
        for angle in self.angles:
            img = TF.rotate(image, angle)
            images[count] = img
            count+=1
        return images

    def save_pickle(self, tensor, path, filename):
        torch.save(tensor, os.path.join(path, filename))

    def create_directories(self):
        if not os.path.exists(self.store_path):
            os.makedirs(self.store_path)



if __name__ == '__main__':

    dataset = SegDataset(raw_path='/home/aymane/School/pothole-localization/data/segmentation/raw')

    print(dataset[0])
            




    