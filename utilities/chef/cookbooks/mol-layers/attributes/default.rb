#
# Cookbook Name:: mol
# Recipe:: default
# Author:: Andrew W. Hill (<andrewxhill@gmail.com>)
#
# Copyright 2011, Andrew W. Hill
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

default[:mol][:node_existed] = true
default[:mol][:repo] = "https://github.com/andrewxhill/MOL.git"
default[:mol][:checkout_point] = "master"
default[:mol][:base_dir] = "/MOL"
default[:mol][:remote_data_checkout_point] = "/mol-data"
default[:mol][:remote_data_repo] = "http://mol.colorado.edu/mol-data"
default[:mol][:remote_data_branch] = "master"
default[:mol][:ini_file] = "development.ini"
default[:mol][:layers_port] = "5003"
