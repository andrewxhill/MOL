#
# Cookbook Name:: gdal
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
 
package "curl"

execute "download and compile GDAL source" do
  cwd "/usr/local/src"
  command "mkdir -p gdal-v#{node[:gdal][:version]} && \
           cd gdal-v#{node[:gdal][:version]} && \
           curl -L http://download.osgeo.org/gdal/gdal-#{node[:gdal][:version]}.tar.gz | tar xzf - --strip-components=1 && \
           ./configure && \
           make && \
           make install"
  not_if {File.exists?("/usr/local/src/gdal-v#{node[:gdal][:version]}")}
end

