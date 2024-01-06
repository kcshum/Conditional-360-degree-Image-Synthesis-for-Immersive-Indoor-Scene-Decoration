from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union, Dict

from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.transforms import InterpolationMode

from data.nodata import NullIterableDataset
from data.utils import ImageFolderWithFilenames
from utils import print_once

_all__ = ['ImageFolderDataModule']


@dataclass
class ImageFolderDataModule(LightningDataModule):
    path: Union[str, Path]  # Root
    dataloader: Dict[str, Any]
    resolution: int = 256  # Image dimension

    def __post_init__(self):
        super().__init__()
        self.path = Path(self.path)
        self.stats = {'mean': (0.5, 0.5, 0.5), 'std': (0.5, 0.5, 0.5)}
        self.transform = transforms.Compose([
            t for t in [
                transforms.Resize([self.resolution, self.resolution], InterpolationMode.LANCZOS),
                transforms.CenterCrop(self.resolution),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(self.stats['mean'], self.stats['std'], inplace=True),
            ]
        ])
        self.data = {}

    def setup(self, stage: Optional[str] = None):
        for split in ('train', 'validate', 'test'):
            path = self.path / split
            empty = True
            if path.exists():
                try:
                    print('trying to make dataset...')
                    self.data[split] = ImageFolderWithFilenames(path, transform=self.transform)
                    empty = False
                except FileNotFoundError:
                    print('FileNotFoundError')
                    pass
            if empty:
                print_once(
                    f'Warning: no images found in {path}. Using empty dataset for split {split}. '
                    f'Perhaps you set `dataset.path` incorrectly?')
                self.data[split] = NullIterableDataset(1)

    def train_dataloader(self) -> DataLoader:
        return self._get_dataloader('train')

    def val_dataloader(self) -> DataLoader:
        return self._get_dataloader('validate')

    def test_dataloader(self) -> DataLoader:
        return self._get_dataloader('test')

    def _get_dataloader(self, split: str):
        return DataLoader(self.data[split], **self.dataloader)
