#
# Cookbook Name:: windshaft
# Recipe:: default
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

include_recipe "build-essential"
include_recipe "git"
include_recipe "nodejs"
include_recipe "nodejs::npm"
include_recipe "redis"
include_recipe 'postgis'

# Install Mapnik dependencies for Windshaft (the hacky way).
# 
# As of October 1, 2011, Windshaft isn't working with Mapnik HEAD. It does work
# with Mapnik r3272, so this resource downloads and installs the following .deb 
# files (along with all dependencies) from a nightly build of r3272:
#
# libicu42_4.2.1-3_amd64.deb                               
# mapnik2-doc_2+dev20110905.svn3272-1~lucid1_all.deb
# libmapnik2_2+dev20110905.svn3272-1~lucid1_amd64.deb      
# mapnik2-utils_2+dev20110905.svn3272-1~lucid1_amd64.deb
# libmapnik2-dev_2+dev20110905.svn3272-1~lucid1_amd64.deb
#
execute "install mapnik dependencies" do
  cwd "/usr/local/src"
  command "wget http://dl.dropbox.com/u/13724811/mapnik-deps.tar.gz && \
           tar xvfz mapnik-deps.tar.gz && \
           cd mapnik && \
           apt-get install -y gdebi && \
           gdebi -n libicu42_4.2.1-3_amd64.deb && \
           gdebi -n libmapnik2_2+dev20110905.svn3272-1~lucid1_amd64.deb && \
           gdebi -n mapnik2-utils_2+dev20110905.svn3272-1~lucid1_amd64.deb && \
           gdebi -n libmapnik2-dev_2+dev20110905.svn3272-1~lucid1_amd64.deb &&"
  not_if {File.exists?("/usr/local/src/mapnik")}
end

# Install Windshaft.
#
# This resources clones the Windshaft git repo and installs tag  0.0.11 which is 
# the production tag used by CartoDB.
#
execute "Install Windshaft" do
  cwd "/usr/local"
  command "git clone #{node[:ws][:repo]} #{node[:ws][:dir]} && \
           cd #{node[:ws][:dir]} && \
           git checkout #{node[:ws][:repo_tag]} && \
           npm install ."
  not_if {File.exists?("#{node[:ws][:dir]}")}
end

# Install forever
#
execute "Install forever" do
  cwd "/usr/local"
  command "npm install -g forever"
  not_if "which forever"
end

# Build init.d script for Windshaft
#
template "windshaft" do
  path "#{node[:ws][:service]}"
  source "windshaft.erb"
  owner "root"
  group "root"
  mode 0755
  not_if { FileTest.exists?("#{node[:ws][:service]}") }
end

# Define Windshaft service
#
service "windshaft" do
  service_name #{node[:ws][:service]}
  supports :status => false, :restart => true, :reload => false
  action [ :enable, :stop, :start ]
end
