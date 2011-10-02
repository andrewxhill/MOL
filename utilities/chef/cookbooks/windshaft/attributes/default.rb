#
# Cookbook Name:: windshaft
# Recipe:: default
# Author:: Aaron Steele (<eightysteele@gmail.com>)
#
# Copyright 2011, Aaron Steele
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

default[:ws][:dir] = "/usr/local/windshaft"
default[:ws][:repo] = "https://github.com/Vizzuality/Windshaft.git"
default[:ws][:repo_tag] = "0.0.11"
default[:ws][:service] = "/etc/init.d/windshaft"


