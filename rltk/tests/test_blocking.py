import pytest

from rltk.record import Record
from rltk.dataset import Dataset
from rltk.io.reader.array_reader import ArrayReader
from rltk.blocking.block_black_list import BlockBlackList
from rltk.blocking.hash_block_generator import HashBlockGenerator
from rltk.blocking.token_block_generator import TokenBlockGenerator
from rltk.blocking.canopy_block_generator import CanopyBlockGenerator


class ConcreteRecord(Record):
   @property
   def id(self):
       return self.raw_object['id']

   @property
   def name(self):
       return self.raw_object['name']

   @property
   def category(self):
       return self.raw_object['category']


raw_data = [
    {'id': '1', 'name': 'apple', 'category': 'a'},
    {'id': '2', 'name': 'banana', 'category': 'a'},
    {'id': '3', 'name': 'apple & banana', 'category': 'b'},
    {'id': '4', 'name': 'pineapple', 'category': 'b'},
    {'id': '5', 'name': 'peach', 'category': 'b'},
    {'id': '6', 'name': 'coconut', 'category': 'b'}
]

ds = Dataset(reader=ArrayReader(raw_data), record_class=ConcreteRecord)


def test_hash_block_generator():
    bg = HashBlockGenerator()
    block = bg.block(ds, property_='category')
    for key, set_ in block.key_set_adapter:
        if key == 'a':
            assert set_ == set([(ds.id, '1'), (ds.id, '2')])
        elif key == 'b':
            assert set_ == set([(ds.id, '3'), (ds.id, '4'), (ds.id, '5'), (ds.id, '6')])
    block = bg.block(ds, function_=lambda r: r.category)
    for key, set_ in block.key_set_adapter:
        if key == 'a':
            assert set_ == set([(ds.id, '1'), (ds.id, '2')])
        elif key == 'b':
            assert set_ == set([(ds.id, '3'), (ds.id, '4'), (ds.id, '5'), (ds.id, '6')])

    block_black_list = BlockBlackList(max_size=2)
    block = bg.block(ds, property_='category', block_black_list=block_black_list)
    for key, set_ in block.key_set_adapter:
        assert key == 'a'
    for key, _ in block_black_list.key_set_adapter:
        assert key == 'b'


def test_token_block_generator():
    bg = TokenBlockGenerator()
    block = bg.block(ds, function_=lambda r: r.name.split(' '))
    for key, set_ in block.key_set_adapter:
        if key == 'apple':
            assert set_ == set([(ds.id, '1'), (ds.id, '3')])
        elif key == 'banana':
            assert set_ == set([(ds.id, '2'), (ds.id, '3')])

    block_black_list = BlockBlackList(max_size=1)
    block = bg.block(ds, function_=lambda r: r.name.split(' '), block_black_list=block_black_list)
    for key, set_ in block.key_set_adapter:
        assert len(set_) <= 1
    for key, _ in block_black_list.key_set_adapter:
        assert key in ('apple', 'banana')


def test_canopy_block_generator():
    bg = CanopyBlockGenerator(t1=5, t2=1, distance_metric=lambda x, y: abs(x[0] - y[0]))
    block = bg.block(ds, function_=lambda r: [ord(r.name[0].lower()) - 0x61])
    output_block = bg.generate(block, block)
    for k, _ in output_block.key_set_adapter:
        assert k in ('[1]', '[2]', '[0]', '[15]')
