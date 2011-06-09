#
# Cookbook Name:: pylons
# Recipe:: default
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
include_recipe "git"

# create base MOL directory on node
directory "#{node[:mol][:base_dir]}" do
  owner 'root'
  group 'root'
  mode 0755
  recursive true
end
# download mol source and checkout specific version/branch
execute "fetch MOL from GitHub" do
  command "git clone https://github.com/andrewxhill/MOL.git #{node[:mol][:base_dir]}"
  not_if { FileTest.exists?(node[:mol][:base_dir]) }
end
execute "use branch of MOL" do
  command "cd #{node[:mol][:base_dir]} && git checkout #{node[:mol][:branch]}"
  not_if { FileTest.exists?(node[:mol][:base_dir]) }
end
