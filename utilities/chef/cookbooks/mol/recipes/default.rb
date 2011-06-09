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
include_recipe "nginx"

package "python-gdal" do
  action :install
end
package "python-mapnik" do
  action :install
end
#enable the layers app site in nginx
template "#{node[:nginx][:dir]}/sites-enabled/layers" do
  source "layers-site.erb"
  owner "root"
  group "root"
  mode 0644
end
#setup init.d script for the layers pylons app
template "layers" do
  path "/etc/init.d/layers"
  source "layers.erb"
  owner "root"
  group "root"
  mode 0755
end
# remove existing directory if needed
execute "remove MOL dir" do
  command "rm -r #{node[:mol][:base_dir]}"
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

# get ownship of base MOL directory on node
directory "#{node[:mol][:base_dir]}" do
  owner 'root'
  group 'root'
  mode 0755
  recursive true
end
#restart services
service "nginx" do
  supports :status => true, :restart => true, :reload => true
  action [ :enable, :start, :restart ]
end
service "layers" do
  supports :status => false, :restart => true, :reload => false
  action [ :enable, :start ]
end
