#
# Cookbook Name:: starspan
# Recipe:: default
#
# Copyright 2010, ProtectedPlanet.net
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
#include_recipe 'ssh'
include_recipe 'gdal'
include_recipe 'geos'

remote_file "download_starspan" do
  path "/tmp/starspan.tar.gz"
  source "http://github.com/tokumine/Starspan/tarball/1.0.08g"
end 
 
 # remove with dpkg -r starspan
bash "install_starspan" do
  user "root"
  cwd "/tmp"
  code <<-EOH    
  tar zxvf starspan.tar.gz
  cd /tmp/tokumine-Starspan*
  ./configure
  make
  checkinstall --pkgname starspan --pkgversion 1.0.08g-src --default 
  EOH
  only_if { `which starspan`.empty?}
end 