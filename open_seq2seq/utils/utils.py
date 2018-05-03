# Copyright (c) 2017 NVIDIA Corporation
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from six.moves import range
from six import string_types

import tensorflow as tf
import subprocess


def get_git_hash():
  try:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                   stderr=subprocess.STDOUT).decode()
  except subprocess.CalledProcessError as e:
    return "{}\n".format(e.output.decode("utf-8"))


def get_git_diff():
  try:
    return subprocess.check_output(['git', 'diff'],
                                   stderr=subprocess.STDOUT).decode()
  except subprocess.CalledProcessError as e:
    return "{}\n".format(e.output.decode("utf-8"))


class Logger(object):
  def __init__(self, stream, log_file):
    self.stream = stream
    self.log = log_file

  def write(self, msg):
    self.stream.write(msg)
    self.log.write(msg)

  def flush(self):
    self.stream.flush()
    self.log.flush()


def flatten_dict(dct):
  flat_dict = {}
  for key, value in dct.items():
    if isinstance(value, int) or isinstance(value, float) or \
       isinstance(value, string_types) or isinstance(value, bool):
      flat_dict.update({key: value})
    elif isinstance(value, dict):
      flat_dict.update(
        {key + '/' + k: v for k, v in flatten_dict(dct[key]).items()})
  return flat_dict


def nest_dict(flat_dict):
  nst_dict = {}
  for key, value in flat_dict.items():
    nest_keys = key.split('/')
    cur_dict = nst_dict
    for i in range(len(nest_keys) - 1):
      if nest_keys[i] not in cur_dict:
        cur_dict[nest_keys[i]] = {}
      cur_dict = cur_dict[nest_keys[i]]
    cur_dict[nest_keys[-1]] = value
  return nst_dict


def nested_update(org_dict, upd_dict):
  for key, value in upd_dict.items():
    if isinstance(value, dict):
      nested_update(org_dict[key], value)
    else:
      org_dict[key] = value


def mask_nans(x):
  x_zeros = tf.zeros_like(x)
  x_mask = tf.is_finite(x)
  y = tf.where(x_mask, x, x_zeros)
  return y


def deco_print(line, offset=0, start="*** ", end='\n'):
  print(start + " " * offset + line, end=end)


def array_to_string(row, vocab, delim=' '):
  n = len(vocab)
  return delim.join(map(lambda x: vocab[x], [r for r in row if 0 <= r < n]))


def text_ids_to_string(row, vocab, S_ID, EOS_ID, PAD_ID,
                       ignore_special=False, delim=' '):
  """For _-to-text outputs this function takes a row with ids,
  target vocabulary and prints it as a human-readable string
  """
  n = len(vocab)
  if ignore_special:
    f_row = []
    for i in range(0, len(row)):
      char_id = row[i]
      if char_id == EOS_ID:
        break
      if char_id != PAD_ID and char_id != S_ID:
        f_row += [char_id]
    return delim.join(map(lambda x: vocab[x], [r for r in f_row if 0 < r < n]))
  else:
    return delim.join(map(lambda x: vocab[x], [r for r in row if 0 < r < n]))


def check_params(config, required_dict, optional_dict):
  if required_dict is None or optional_dict is None:
    return

  for pm, vals in required_dict.items():
    if pm not in config:
      raise ValueError("{} parameter has to be specified".format(pm))
    else:
      if vals == str:
        vals = string_types
      if vals and isinstance(vals, list) and config[pm] not in vals:
        raise ValueError("{} has to be one of {}".format(pm, vals))
      if vals and not isinstance(vals, list) and not isinstance(config[pm], vals):
        raise ValueError("{} has to be of type {}".format(pm, vals))

  for pm, vals in optional_dict.items():
    if vals == str:
      vals = string_types
    if pm in config:
      if vals and isinstance(vals, list) and config[pm] not in vals:
        raise ValueError("{} has to be one of {}".format(pm, vals))
      if vals and not isinstance(vals, list) and not isinstance(config[pm], vals):
        raise ValueError("{} has to be of type {}".format(pm, vals))

  for pm in config:
    if pm not in required_dict and pm not in optional_dict:
      raise ValueError("Unknown parameter: {}".format(pm))


def cast_types(input_dict, dtype):
  cast_input_dict = {}
  for key, value in input_dict.items():
    if isinstance(value, tf.Tensor):
      if value.dtype == tf.float16 or value.dtype == tf.float32:
        if value.dtype.base_dtype != dtype.base_dtype:
          cast_input_dict[key] = tf.cast(value, dtype)
          continue
    if type(value) == dict:
      cast_input_dict[key] = cast_types(input_dict[key], dtype)
      continue
    cast_input_dict[key] = input_dict[key]
  return cast_input_dict
