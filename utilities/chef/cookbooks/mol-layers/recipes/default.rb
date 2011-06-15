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
# download mol source and checkout specific version/branch
execute "fetch MOL from GitHub" do
  command "git clone #{node[:mol][:repo]} #{node[:mol][:base_dir]}"
  node.set['mol']['node_existed'] = false
  not_if { FileTest.exists?(node[:mol][:base_dir]) }
end
execute "switch to specified branch/tag of MOL" do
  command "cd #{node[:mol][:base_dir]} && git checkout #{node[:mol][:checkout_point]}"
  not_if { node[:mol][:node_existed] }
end
execute "pull updates of MOL" do
  command "cd #{node[:mol][:base_dir]} && git pull #{node[:mol][:repo]} #{node[:mol][:checkout_point]}"
end
# set ownership of base MOL directory on node
directory "#{node[:mol][:base_dir]}" do
  owner 'root'
  group 'root'
  mode 0755
  recursive true
  not_if { node[:mol][:node_existed] }
end
# download mol source and checkout specific version/branch
execute "fetch data from git data repo" do
  command "git clone  #{node[:mol][:remote_data_repo]} #{node[:mol][:base_data_dir]}"
  node.set['mol']['node_existed'] = false
  not_if { FileTest.exists?(node[:mol][:base_data_dir]) }
end
execute "switch to specified branch/tag of data repo" do
  command "cd #{node[:mol][:base_data_dir]} && git checkout #{node[:mol][:remote_data_checkout_point]}"
end
execute "pull updates of data repo" do
  command "cd #{node[:mol][:base_data_dir]} && git pull #{node[:mol][:remote_data_repo]} #{node[:mol][:remote_data_checkout_point]}"
end
# set ownership of base mol-data directory on node
directory "#{node[:mol][:base_data_dir]}" do
  owner 'root'
  group 'root'
  mode 0755
  recursive true
  not_if { node[:mol][:node_existed] }
end
#enable the layers app site in nginx
template "#{node[:nginx][:dir]}/sites-enabled/layers" do
  source "layers-site.erb"
  owner "root"
  group "root"
  mode 0644
  not_if { FileTest.exists?("#{node[:nginx][:dir]}/sites-enabled/layers") }
end
#setup init.d script for the layers pylons app
template "layers" do
  path "/etc/init.d/layers"
  source "layers.erb"
  owner "root"
  group "root"
  mode 0755
  not_if { FileTest.exists?("/etc/init.d/layers") }
end
#restart services
service "nginx" do
  supports :status => true, :restart => true, :reload => true
  action [ :enable, :stop, :start ]
end
service "layers" do
  supports :status => false, :restart => true, :reload => false
  action [ :enable, :stop, :start ]
end
