#
# Cookbook Name:: shorewall
# Recipe:: default
#
# Copyright 2010, Sean Carey
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


=begin 

This cookbook was created to install shorewall on ubuntu and iterate through a firewall node attribute. 
More information and a writeup about this cookbook can be found at:

http://densone.com

This cookbook by default is setup to work on RackSpace cloud. RackSpace cloud has an internal and an external interface. 
The policy allow eth1 the internal interface to speak to any ip address. You may want to template the other shorewall config files if 
you plan on deploying this cookbook to other places. This would be a simple task.

=end


package "shorewall"


cookbook_file "/etc/default/shorewall" do
  source "shorewall-enable"
  mode 0644
  owner "root"
  group "root"
end

config_path = "/etc/shorewall"

cookbook_file "#{config_path}/shorewall.conf" do
  source "shorewall.conf"
  mode 0644
  owner "root"
  group "root"
end

cookbook_file "#{config_path}/interfaces" do
  source "interfaces"
  mode 0644
  owner "root"
  group "root"
end

cookbook_file "#{config_path}/zones" do
  source "zones"
  mode 0644
  owner "root"
  group "root"
end

cookbook_file "#{config_path}/policy" do
  source "policy"
  mode 0644
  owner "root"
  group "root"
end

template "#{config_path}/rules" do
  source "rules.erb"
  mode 0644
  owner "root"
  group "root"
  variables(:rule_list => node[:config][:firewall][:rules])
end

service "shorewall" do
  supports :restart => true
  action :enable
  subscribes :restart, resources(:cookbook_file => "#{config_path}/shorewall.conf",
                                 :cookbook_file => "#{config_path}/interfaces", 
                                 :cookbook_file => "#{config_path}/zones", 
                                 :cookbook_file => "#{config_path}/policy", 
                                 :template      => "#{config_path}/rules"), :immediately
end
